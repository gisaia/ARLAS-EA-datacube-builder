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
import concurrent.futures

from models.rasterDrivers.archiveTypes import ArchiveTypes
from models.rasterDrivers.sentinel2_level2A_safe import Sentinel2_Level2A_safe
from models.rasterDrivers.sentinel2_level2A_theia \
    import Sentinel2_Level2A_Theia

from models.request.datacube_build \
    import DATACUBE_BUILD_REQUEST, DatacubeBuildRequest
from models.request.rasterGroup import RASTERGROUP_MODEL
from models.request.band import BAND_MODEL
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
from utils.xarray import getBounds, getChunkShape, mergeDatasets

from urllib.parse import urlparse

api = Namespace("cube",
                description="Build a data cube from raster files")
api.models[DATACUBE_BUILD_REQUEST.name] = DATACUBE_BUILD_REQUEST
api.models[RASTERGROUP_MODEL.name] = RASTERGROUP_MODEL
api.models[BAND_MODEL.name] = BAND_MODEL
api.models[RASTERFILE_MODEL.name] = RASTERFILE_MODEL

api.models[DATACUBE_BUILD_RESPONSE.name] = DATACUBE_BUILD_RESPONSE

TMP_DIR = "tmp/"


def download(download_input: Tuple[DatacubeBuildRequest, int, int]) \
                -> Dict[float, List[str]]:
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
                request.productBands, request.targetResolution,
                timestamp, TMP_DIR)
        elif archiveType == ArchiveTypes.S2L2A_THEIA.value:
            rasterArchive = Sentinel2_Level2A_Theia(
                inputObjectStore, rasterFile.path,
                request.productBands, request.targetResolution,
                timestamp, TMP_DIR)
        else:
            raise DownloadError(f"Archive type '{archiveType}' not accepted")

        api.logger.info(f"[group-{groupIdx}:file-{fileIdx}] Building ZARR")
        # Build the zarr dataset and add it to its group's list
        zarrRootPath = path.join(TMP_DIR, f"{request.dataCubePath}",
                                 f'{groupIdx}/{fileIdx}')
        zarrPath = rasterArchive.buildZarr(
            zarrRootPath, request.targetProjection, polygon=request.roi)

        groupedDatasets: Dict[int, List[str]] = {timestamp: [zarrPath]}
        return groupedDatasets
    except Exception as e:
        api.logger.error(f"[group-{groupIdx}:file-{fileIdx}]")
        raise DownloadError(e.args[0])


def merge_download(result_a: Dict[int, List[str]],
                   result_b: Dict[int, List[str]]) \
                   -> Dict[int, List[str]]:
    """
    Merge the results of the download method in a mapreduce process
    """
    for timestamp in list(result_b.keys()):
        if timestamp in list(result_a.keys()):
            result_a[timestamp].extend(result_b[timestamp])
        else:
            result_a[timestamp] = result_b[timestamp]
    return result_a


def mosaicking(merge_input) -> xr.Dataset:
    listAdress = merge_input[0]
    lon = merge_input[1]
    lat = merge_input[2]
    lonStep = merge_input[3]
    latStep = merge_input[4]

    mergedDataset = None
    for dsAdress in listAdress:
        # Interpolate the granule with new grid on its extent
        with xr.open_zarr(dsAdress) as dataset:
            bounds = getBounds(dataset)
            granuleGrid = {}
            granuleGrid["x"] = lon[(lon[:] >= bounds[0])
                                   & (lon[:] <= bounds[2])]
            granuleGrid["y"] = lat[(lat[:] >= bounds[1])
                                   & (lat[:] <= bounds[3])]
            granuleGrid["x"], granuleGrid["y"] = completeGrid(
                granuleGrid["x"], lonStep,
                granuleGrid["y"], latStep,
                bounds)

            mergedDataset = mergeDatasets(
                mergedDataset,
                dataset.interp_like(
                    xr.Dataset(granuleGrid),
                    method="nearest"
                )
            )

    return mergedDataset


def merge_mosaicking(mosaick_a: xr.Dataset,
                     mosaick_b: xr.Dataset) -> xr.Dataset:
    return xr.combine_by_coords(
        (mosaick_a, mosaick_b), combine_attrs="override")


def post_cube_build(request: DatacubeBuildRequest):

    groupedDatasets: dict[int, List[str]] = {}

    centerGranuleIdx = {"group": int, "index": int}
    xmin, ymin, xmax, ymax = np.inf, np.inf, -np.inf, -np.inf
    roiCentroid: Point = request.roi.centroid
    minDistance = np.inf

    zarrRootPath = path.join(TMP_DIR, request.dataCubePath)

    # Generate the iterable of all files to download
    mapReduceIter = []
    for groupIdx in range(len(request.composition)):
        for idx in range(len(request.composition[groupIdx].rasters)):
            mapReduceIter.append((request, groupIdx, idx))

    # Download parallely the groups of bands of each file
    try:
        with mr4mp.pool(close=True) as pool:
            groupedDatasets = pool.mapreduce(
                download, merge_download, mapReduceIter)
    except DownloadError as e:
        return e

    for timestamp, datasetList in groupedDatasets.items():
        for idx, dsAdress in enumerate(datasetList):
            # Find the centermost granule based on ROI and max bounds
            with xr.open_zarr(dsAdress) as dataset:
                dsBounds = getBounds(dataset)
                granuleCenter = Point((dsBounds[0] + dsBounds[2])/2,
                                      (dsBounds[1] + dsBounds[3])/2)
                if roiCentroid.distance(granuleCenter) < minDistance:
                    minDistance = roiCentroid.distance(granuleCenter)
                    centerGranuleIdx["group"] = timestamp
                    centerGranuleIdx["index"] = idx

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
            with xr.open_zarr(groupedDatasets[centerGranuleIdx["group"]][
                        centerGranuleIdx["index"]]) as centerGranuleDs:
                lonStep = centerGranuleDs.get("x").diff("x").mean()
                latStep = centerGranuleDs.get("y").diff("y").mean()

                lon, lat = completeGrid(
                    centerGranuleDs.get("x"), lonStep,
                    centerGranuleDs.get("y"), latStep,
                    (xmin, ymin, xmax, ymax))

            # For each time bucket, create a mosaick of the datasets
            timestamps = list(groupedDatasets.keys())
            timestamps.sort()

            iterMosaicking = []
            for t in timestamps:
                iterMosaicking.append([groupedDatasets[t], lon, lat,
                                       lonStep, latStep])

            with mr4mp.pool(close=True) as pool:
                datacube = pool.mapreduce(mosaicking, merge_mosaicking,
                                          iterMosaicking)

        except Exception as e:
            api.logger.error(e)
            traceback.print_exc()
            return MosaickingError(e.args[0])
    else:
        firstDataset = groupedDatasets[list(groupedDatasets.keys())[0]][0]
        with xr.open_zarr(firstDataset) as ds:
            datacube = ds
    # TODO: merge manually dataset attributes

    # Compute the bands requested from the product bands
    for band in request.bands:
        if band.value is not None:
            datacube[band.name] = eval(band.value)

    # Keep just the bands requested
    requestedBands = [band.name for band in request.bands]

    api.logger.info("Writing datacube to Object Store")
    try:
        datacubeUrl, mapper = getMapperOutputObjectStore(
            request.dataCubePath)

        datacube[requestedBands] \
            .chunk(
                getChunkShape(datacube.dims, request.chunkingStrategy)) \
            .to_zarr(mapper, mode="w") \
            .close()

    except Exception as e:
        api.logger.error(e)
        traceback.print_exc()
        return UploadError(f"Datacube: {e.args[0]}")

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
            if "B2" in request.productBands \
                    and "B3" in request.productBands \
                    and "B4" in request.productBands:
                previewBands = {
                    RGB.RED: "B4", RGB.GREEN: "B3", RGB.BLUE: "B2"}
            elif "B02" in request.productBands \
                    and "B03" in request.productBands \
                    and "B04" in request.productBands:
                previewBands = {
                    RGB.RED: "B04", RGB.GREEN: "B03", RGB.BLUE: "B02"}
            else:
                firstBand: str = request.bands[0].name
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
        return UploadError(f"Preview: {e.args[0]}")

    # Clean up the files created
    del datacube
    if os.path.exists(zarrRootPath) and os.path.isdir(zarrRootPath):
        shutil.rmtree(zarrRootPath)
    os.remove(f'{zarrRootPath}.png')
    os.remove(f'{zarrRootPath}.png.aux.xml')

    return DatacubeBuildResponse(
        datacubeUrl, f"{datacubeUrl}.png", preview)


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

        with concurrent.futures.ProcessPoolExecutor() as executor:
            f = executor.submit(post_cube_build, request)
            result = f.result()

        if issubclass(type(result), AbstractError):
            raise result

        return result, HTTPStatus.OK
