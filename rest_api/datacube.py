#!/usr/bin/python3
from typing import List, Dict, Tuple
import traceback

import base64
import os
import os.path as path
import shutil
import numpy as np
import xarray as xr
from flask_restx import Namespace, Resource
from shapely.geometry import Point
import smart_open as so
import mr4mp
from http import HTTPStatus

from models.rasterDrivers.archiveTypes import ArchiveTypes
from models.rasterDrivers.sentinel2_level2A_safe import Sentinel2_Level2A_safe
from models.rasterDrivers.sentinel2_level2A_theia \
    import Sentinel2_Level2A_Theia

from models.request.datacube_build \
    import DATACUBE_BUILD_REQUEST, DatacubeBuildRequest
from models.request.rasterGroup import RASTERGROUP_MODEL
from models.request.asset import ASSET_MODEL
from models.request.rasterFile import RASTERFILE_MODEL

from models.response.datacube_build import DATACUBE_BUILD_RESPONSE, \
                                           DatacubeBuildResponse
from models.errors import BadRequest, DownloadError, \
                          MosaickingError, UploadError

from utils.enums import RGB
from utils.geometry import completeGrid
from utils.objectStore import createInputObjectStore, \
                              getMapperOutputObjectStore, \
                              createOutputObjectStore
from utils.preview import createPreviewB64
from utils.xarray import getBounds, getChunkSize, mergeDatasets

from urllib.parse import urlparse

api = Namespace("cube",
                description="Build a data cube from raster files")
api.models[DATACUBE_BUILD_REQUEST.name] = DATACUBE_BUILD_REQUEST
api.models[RASTERGROUP_MODEL.name] = RASTERGROUP_MODEL
api.models[ASSET_MODEL.name] = ASSET_MODEL
api.models[RASTERFILE_MODEL.name] = RASTERFILE_MODEL

api.models[DATACUBE_BUILD_RESPONSE.name] = DATACUBE_BUILD_RESPONSE

TMP_DIR = "tmp/"


def download(download_input: Tuple[DatacubeBuildRequest, int, int]) \
                -> Dict[float, List[xr.Dataset]]:
    """
    Builds a zarr corresponding to the requested bands for
    the raster file 'fileIdx' in the group 'groupIdx'
    """
    request = download_input[0]
    groupIdx = download_input[1]
    fileIdx = download_input[2]

    try:
        # Retrieve from the request the important information
        rasterFile = request.composition[groupIdx].rasters[fileIdx]
        timestamp = request.composition[groupIdx].timestamp

        inputObjectStore = createInputObjectStore(
                        urlparse(rasterFile.path).scheme)
        archiveType = rasterFile.source + "-" + rasterFile.format

        api.logger.info(f"[group-{groupIdx}:file-{fileIdx}] Extracting bands")
        # Depending on archive type, extract desired data
        if archiveType == ArchiveTypes.S2L2A.value:
            rasterArchive = Sentinel2_Level2A_safe(
                inputObjectStore, rasterFile.path,
                request.bands, request.targetResolution,
                timestamp, TMP_DIR)
        elif archiveType == ArchiveTypes.S2L2A_THEIA.value:
            rasterArchive = Sentinel2_Level2A_Theia(
                inputObjectStore, rasterFile.path,
                request.bands, request.targetResolution,
                timestamp, TMP_DIR)
        else:
            raise DownloadError(f"Archive type '{archiveType}' not accepted")

        api.logger.info(f"[group-{groupIdx}:file-{fileIdx}] Building ZARR")
        # Build the zarr dataset and add it to its group's list
        dataset = rasterArchive.buildZarr(
            path.join(TMP_DIR, request.dataCubePath, f'{groupIdx}/{fileIdx}'),
            request.targetProjection, polygon=request.roi)

        groupedDatasets: Dict[int, List[xr.Dataset]] = {timestamp: [dataset]}
        return groupedDatasets
    except Exception as e:
        api.logger.error(f"[group-{groupIdx}:file-{fileIdx}]")
        raise DownloadError(e.args[0])


def merge(result_a: Dict[int, List[xr.Dataset]],
          result_b: Dict[int, List[xr.Dataset]]) \
            -> Dict[int, List[xr.Dataset]]:
    """
    Merge the results of the download method in a mapreduce process
    """
    for timestamp in list(result_b.keys()):
        if timestamp in list(result_a.keys()):
            result_a[timestamp].extend(result_b[timestamp])
        else:
            result_a[timestamp] = result_b[timestamp]
    return result_a


@api.route('/build')
class DataCube_Build(Resource):

    @api.expect(DATACUBE_BUILD_REQUEST)
    @api.marshal_with(DATACUBE_BUILD_RESPONSE)
    def post(self):
        api.logger.info("[POST] /build")

        try:
            request = DatacubeBuildRequest(**api.payload)
        except Exception as e:
            raise BadRequest(e.args[0])

        groupedDatasets: dict[int, List[xr.Dataset]] = {}

        centerMostGranule = {"group": int, "index": int}
        xmin, ymin, xmax, ymax = np.inf, np.inf, -np.inf, -np.inf
        roiCentroid: Point = request.roi.centroid
        minDistance = np.inf

        zarrRootPath = path.join(TMP_DIR, request.dataCubePath)

        # Generate the iterable of all files to download
        mapReduceIter = []
        for groupIdx in range(len(request.composition)):
            for idx in range(len(request.composition[groupIdx].rasters)):
                mapReduceIter.append((request, groupIdx, idx))

        # Download paralelly the groups of bands of each file
        try:
            pool = mr4mp.pool()
            groupedDatasets = pool.mapreduce(download, merge, mapReduceIter)
            pool.close()
        except DownloadError as e:
            raise e

        for timestamp, datasetList in groupedDatasets.items():
            for idx, dataset in enumerate(datasetList):
                # Find the centermost granule based on ROI and max bounds
                dsBounds = getBounds(dataset)
                granuleCenter = Point((dsBounds[0] + dsBounds[2])/2,
                                      (dsBounds[1] + dsBounds[3])/2)
                if roiCentroid.distance(granuleCenter) < minDistance:
                    minDistance = roiCentroid.distance(granuleCenter)
                    centerMostGranule["group"] = timestamp
                    centerMostGranule["index"] = idx

                # Update the extent of the datacube
                xmin = min(xmin, dsBounds[0])
                ymin = min(ymin, dsBounds[1])
                xmax = max(xmax, dsBounds[2])
                ymax = max(ymax, dsBounds[3])

        api.logger.info("Building datacube from the ZARRs")
        # If there is more than one file requested
        if not (len(request.composition) == 1 and
                len(request.composition[0].rasters) == 1):
            try:
                # Generate a grid extending the center granule
                centerMostGranuleDS: xr.Dataset = groupedDatasets[
                    centerMostGranule["group"]][centerMostGranule["index"]]
                lonStep = centerMostGranuleDS.get("x").diff("x").mean()
                latStep = centerMostGranuleDS.get("y").diff("y").mean()

                lon, lat = completeGrid(
                    centerMostGranuleDS.get("x"), lonStep,
                    centerMostGranuleDS.get("y"), latStep,
                    (xmin, ymin, xmax, ymax))

                # For each time bucket, create a mosaick of the datasets
                timestamps = list(groupedDatasets.keys())
                timestamps.sort()

                mergedDSPerBucket = []
                for t in timestamps:
                    mergedDataset = None
                    for dataset in groupedDatasets[t]:
                        # Interpolate the granule with new grid on its extent
                        granuleBounds = getBounds(dataset)
                        granuleLon = lon[(lon[:] >= granuleBounds[0])
                                         & (lon[:] <= granuleBounds[2])]
                        granuleLat = lat[(lat[:] >= granuleBounds[1])
                                         & (lat[:] <= granuleBounds[3])]
                        granuleLon, granuleLat = completeGrid(
                            granuleLon, lonStep, granuleLat, latStep,
                            granuleBounds)

                        grid = xr.Dataset({"x": granuleLon, "y": granuleLat})
                        ds = dataset.interp_like(grid, method="nearest")

                        if mergedDataset:
                            mergedDataset = mergeDatasets(mergedDataset, ds)
                        else:
                            mergedDataset = ds
                    mergedDSPerBucket.append(mergedDataset.copy(deep=True))

                datacube: xr.Dataset = xr.concat(mergedDSPerBucket, dim="t")
            except Exception as e:
                api.logger.error(e)
                traceback.print_exc()
                raise MosaickingError(e.args[0])
        else:
            datacube = groupedDatasets[list(groupedDatasets.keys())[0]][0]
        # TODO: merge manually dataset attributes

        # Get the assets requested from the bands
        for asset in request.assets:
            if asset.value is not None:
                datacube[asset.name] = eval(asset.value)

        # Keep just the assets requested
        requestedAssets = [asset.name for asset in request.assets]

        api.logger.info("Writing datacube to Object Store")
        try:
            datacubeUrl, mapper = getMapperOutputObjectStore(
                request.dataCubePath)
            chunkSize = getChunkSize(datacube.attrs['dtype'])
            datacube.get(requestedAssets) \
                    .chunk({"x": chunkSize, "y": chunkSize, "t": 1}) \
                    .to_zarr(mapper, mode="w")
        except Exception as e:
            api.logger.error(e)
            traceback.print_exc()
            raise UploadError(f"Datacube: {e.args[0]}")

        api.logger.info("Uploading preview to Object Store")
        try:
            # If all colors have been assigned, use them
            if request.rgb != {}:
                previewBands = request.rgb
            # Depending on the format of the Sentinel2 files,
            # bands are not named the same. It is not possible
            # to check globally unless columns are standardized.
            # If RGB bands were used to construct composite bands,
            # they are still used for the preview.
            else:
                if "B2" in request.bands and "B3" in request.bands \
                        and "B4" in request.bands:
                    previewBands = {
                        RGB.RED: "B4", RGB.GREEN: "B3", RGB.BLUE: "B2"}
                elif "B02" in request.bands and "B03" in request.bands \
                        and "B04" in request.bands:
                    previewBands = {
                        RGB.RED: "B04", RGB.GREEN: "B03", RGB.BLUE: "B02"}
                else:
                    firstBand: str = request.bands[0]
                    previewBands = {RGB.RED: firstBand,
                                    RGB.GREEN: firstBand,
                                    RGB.BLUE: firstBand}

            preview = createPreviewB64(datacube, previewBands,
                                       f'{zarrRootPath}.png')
            client = createOutputObjectStore().client

            with so.open(f"{datacubeUrl}.png", "wb",
                         transport_params={"client": client}) as fb:
                fb.write(base64.b64decode(preview))
        except Exception as e:
            api.logger.error(e)
            traceback.print_exc()
            raise UploadError(f"Preview: {e.args[0]}")

        # Clean up the files created
        if os.path.exists(zarrRootPath) and os.path.isdir(zarrRootPath):
            shutil.rmtree(zarrRootPath)
        os.remove(f'{zarrRootPath}.png')
        os.remove(f'{zarrRootPath}.png.aux.xml')

        return DatacubeBuildResponse(
            datacubeUrl, f"{datacubeUrl}.png", preview), HTTPStatus.OK
