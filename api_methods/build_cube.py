#!/usr/bin/python3
from typing import List, Dict, Tuple
import traceback

import base64
import os
import os.path as path
import shutil
import numpy as np
import xarray as xr
from shapely.geometry import Point
import smart_open as so
import mr4mp
import concurrent.futures

from models.request.cubeBuild import ExtendedCubeBuildRequest

from models.response.datacube_build import DatacubeBuildResponse
from models.errors import DownloadError, \
                          MosaickingError, UploadError, AbstractError

from utils.enums import ChunkingStrategy as CStrat
from utils.geometry import completeGrid
from utils.logger import CustomLogger as Logger
from utils.metadata import create_datacube_metadata
from utils.objectStore import createInputObjectStore, \
                              getMapperOutputObjectStore, \
                              createOutputObjectStore
from utils.preview import createPreviewB64, createPreviewB64Cmap
from utils.request import getProductBands, getRasterDriver, getEvalFormula
from utils.xarray import getBounds, getChunkShape, mergeDatasets

from urllib.parse import urlparse

TMP_DIR = "tmp/"


def download(input: Tuple[ExtendedCubeBuildRequest, int, int]) \
        -> Dict[float, List[str]]:
    """
    Builds a zarr corresponding to the requested bands for
    the raster file 'fileIdx' in the group 'groupIdx'
    """
    request = input[0]
    groupIdx = input[1]
    fileIdx = input[2]
    logger = Logger.getLogger()

    try:
        # Retrieve from the request the important information
        rasterFile = request.composition[groupIdx].rasters[fileIdx]
        timestamp = request.composition[groupIdx].timestamp

        inputObjectStore = createInputObjectStore(
                        urlparse(rasterFile.path).scheme)

        logger.info(f"[group-{groupIdx}:file-{fileIdx}] Extracting bands")
        # Depending on archive type, extract desired data
        rasterArchive = getRasterDriver(rasterFile.type)(
            inputObjectStore, rasterFile.path,
            getProductBands(request, rasterFile.type),
            request.target_resolution,
            timestamp, TMP_DIR)

        logger.info(f"[group-{groupIdx}:file-{fileIdx}] Building ZARR")
        # Build the zarr dataset and add it to its group's list
        zarrRootPath = path.join(TMP_DIR, f"{request.datacube_path}",
                                 f'{groupIdx}/{fileIdx}')
        zarrPath = rasterArchive.buildZarr(zarrRootPath,
                                           request.target_projection,
                                           polygon=request.roi_polygon)

        groupedDatasets: Dict[int, List[str]] = {timestamp: [zarrPath]}
        return groupedDatasets
    except Exception as e:
        logger.error(f"[group-{groupIdx}:file-{fileIdx}]")
        traceback.print_exc()
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
                granuleGrid["x"], granuleGrid["y"],
                lonStep, latStep, bounds)
            dims = {
                "x": len(granuleGrid["x"]), "y": len(granuleGrid["y"]), "t": 1}

            mergedDataset = mergeDatasets(
                mergedDataset,
                dataset.interp_like(
                    xr.Dataset(granuleGrid), method="nearest")
                .chunk(getChunkShape(dims, CStrat.SPINACH))
            )

    return mergedDataset


def merge_mosaicking(mosaick_a: xr.Dataset,
                     mosaick_b: xr.Dataset) -> xr.Dataset:
    return xr.combine_by_coords(
        (mosaick_a, mosaick_b), combine_attrs="override")


def _build_datacube(request: ExtendedCubeBuildRequest):
    logger = Logger.getLogger()
    groupedDatasets: dict[int, List[str]] = {}

    centerGranuleIdx = {"group": int, "index": int}
    xmin, ymin, xmax, ymax = np.inf, np.inf, -np.inf, -np.inf
    roiCentroid: Point = request.roi_polygon.centroid
    minDistance = np.inf

    zarrRootPath = path.join(TMP_DIR, request.datacube_path)

    # Generate the iterable of all files to download
    mapReduceIter = []
    for groupIdx in range(len(request.composition)):
        for idx in range(len(request.composition[groupIdx].rasters)):
            mapReduceIter.append((request, groupIdx, idx, logger))

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

    logger.info("Building datacube from the ZARRs")
    # If there is more than one file requested
    if not (len(request.composition) == 1 and
            len(request.composition[0].rasters) == 1):
        try:
            # Generate a grid based on the step size of the center granule
            # extending the center of the roi
            with xr.open_zarr(groupedDatasets[centerGranuleIdx["group"]][
                        centerGranuleIdx["index"]]) as centerGranuleDs:
                lonStep = float(centerGranuleDs.get("x").diff("x").mean()
                                .values.tolist())
                latStep = float(centerGranuleDs.get("y").diff("y").mean()
                                .values.tolist())

                lon, lat = completeGrid([roiCentroid.x], [roiCentroid.y],
                                        lonStep, latStep,
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
            logger.error(e)
            traceback.print_exc()
            return MosaickingError(e.args[0])
    else:
        firstDataset = groupedDatasets[list(groupedDatasets.keys())[0]][0]
        with xr.open_zarr(firstDataset) as ds:
            datacube = ds
            lonStep = float(datacube.get("x").diff("x").mean()
                            .values.tolist())
            latStep = float(datacube.get("y").diff("y").mean()
                            .values.tolist())
    # TODO: merge manually dataset attributes

    # Compute the bands requested from the product bands
    for band in request.bands:
        datacube[band.name] = eval(
            getEvalFormula(band.value, request.product_aliases))
        if band.min is not None and band.max is not None:
            datacube[band.name] = datacube[band.name].clip(band.min, band.max)

    # Keep just the bands requested
    requestedBands = [band.name for band in request.bands]
    datacube = datacube[requestedBands]

    # Add relevant datacube metadata
    datacube = create_datacube_metadata(request, datacube, lonStep, latStep)

    logger.info("Writing datacube to Object Store")
    try:
        datacubeUrl, mapper = getMapperOutputObjectStore(
            request.datacube_path)

        datacube.chunk(getChunkShape(
                datacube.dims, request.chunking_strategy)) \
            .to_zarr(mapper, mode="w") \
            .close()

    except Exception as e:
        logger.error(e)
        traceback.print_exc()
        return UploadError(f"Datacube: {e.args[0]}")

    logger.info("Uploading preview to Object Store")
    try:
        if len(datacube.attrs["preview"]) == 3:
            preview = createPreviewB64(datacube, request.rgb,
                                       f'{zarrRootPath}.png')
        else:
            preview = createPreviewB64Cmap(datacube, datacube.attrs["preview"],
                                           f'{zarrRootPath}.png')

        client = createOutputObjectStore().client

        with so.open(f"{datacubeUrl}.png", "wb",
                     transport_params={"client": client}) as fb:
            fb.write(base64.b64decode(preview))
    except Exception as e:
        logger.error(e)
        traceback.print_exc()
        return UploadError(f"Preview: {e.args[0]}")

    # Clean up the files created
    del datacube
    if path.exists(zarrRootPath) and path.isdir(zarrRootPath):
        shutil.rmtree(zarrRootPath)
    os.remove(f'{zarrRootPath}.png')

    return DatacubeBuildResponse(
        datacube_url=datacubeUrl,
        preview_url=f"{datacubeUrl}.png",
        preview=preview)


def build_datacube(request: ExtendedCubeBuildRequest) -> DatacubeBuildResponse:

    with concurrent.futures.ProcessPoolExecutor() as executor:
        f = executor.submit(_build_datacube, request)
        result = f.result()

    if issubclass(type(result), AbstractError):
        raise result

    return result
