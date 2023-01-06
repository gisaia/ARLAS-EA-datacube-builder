#!/usr/bin/python3
from typing import List

import os
import shutil
import numpy as np
import xarray as xr
from flask_restx import Namespace, Resource
from shapely.geometry import Point

from models.rasterDrivers.archiveTypes import ArchiveTypes
from models.rasterDrivers.sentinel2_level2A_safe import Sentinel2_Level2A_safe
from models.rasterDrivers.sentinel2_level2A_theia \
    import Sentinel2_Level2A_Theia
from models.request.datacube_build import DATACUBE_BUILD_REQUEST
from models.request.rasterGroup import RASTERGROUP_MODEL
from models.request.rasterFile import RASTERFILE_MODEL

from utils.geometry import bbox2polygon, completeGrid
from utils.objectStore import createInputObjectStore, \
                              getMapperOutputObjectStore
from utils.xarray import getBounds, getChunkSize, mergeDatasets

from urllib.parse import urlparse

api = Namespace("cube",
                description="Build a data cube from raster files")
api.models[DATACUBE_BUILD_REQUEST.name] = DATACUBE_BUILD_REQUEST
api.models[RASTERGROUP_MODEL.name] = RASTERGROUP_MODEL
api.models[RASTERFILE_MODEL.name] = RASTERFILE_MODEL

ZIP_EXTRACT_PATH = "tmp/"


@api.route('/build')
class DataCube_Build(Resource):

    @api.expect(DATACUBE_BUILD_REQUEST)
    def post(self):
        api.logger.info("[POST] /build")
        rasterGroups: List = api.payload["composition"]

        roi = bbox2polygon(api.payload["roi"]) \
            if "roi" in api.payload \
            else None

        targetResolution = api.payload["targetResolution"] \
            if "targetResolution" in api.payload \
            else 10

        targetProjection = api.payload["tragetProjection"] \
            if "tragetProjection" in api.payload \
            else "EPSG:4326"

        groupedDatasets: dict[float, List[xr.Dataset]] = {}

        centerMostGranule = {"group": float, "index": int}
        xmin, ymin, xmax, ymax = np.inf, np.inf, -np.inf, -np.inf
        roiCentroid: Point = roi.centroid
        minDistance = np.inf

        offset = 1
        zarrRootPath = f'tmp_zarr/{api.payload["dataCubePath"]}'

        for groupIdx, rasterGroup in enumerate(rasterGroups):
            groupedDatasets[rasterGroup["timestamp"]] = []

            for idx, rasterFile in enumerate(rasterGroup["rasters"]):
                api.logger.info(f"[File {idx + offset}] Extracting bands")
                inputObjectStore = createInputObjectStore(
                        urlparse(rasterFile["path"]).scheme)

                archiveType = rasterFile["source"] + "-" + rasterFile["format"]
                try:
                    if archiveType == ArchiveTypes.S2L2A.value:
                        rasterArchive = Sentinel2_Level2A_safe(
                            inputObjectStore, rasterFile["path"],
                            api.payload["bands"], targetResolution,
                            rasterGroup["timestamp"])
                    elif archiveType == ArchiveTypes.S2L2A_THEIA.value:
                        rasterArchive = Sentinel2_Level2A_Theia(
                            inputObjectStore, rasterFile["path"],
                            api.payload["bands"], targetResolution,
                            rasterGroup["timestamp"])
                    else:
                        return f"Archive type '{archiveType}' not accepted", \
                               500
                except Exception as e:
                    api.logger.error(e)
                    return f"Error when extracting bands for {rasterFile}", 500

                try:
                    api.logger.info(f"[File {idx + offset}] Building ZARR")

                    # Build the zarr dataset and add it to its group's list
                    dataset = rasterArchive.buildZarr(
                        f'{zarrRootPath}/{groupIdx}/{idx}',
                        targetProjection, polygon=roi)
                    groupedDatasets[rasterGroup["timestamp"]].append(dataset)

                    # Find the centermost granule based on ROI and max bounds
                    dsBounds = getBounds(dataset)
                    granuleCenter = Point((dsBounds[0] + dsBounds[2])/2,
                                          (dsBounds[1] + dsBounds[3])/2)
                    if roiCentroid.distance(granuleCenter) < minDistance:
                        minDistance = roiCentroid.distance(granuleCenter)
                        centerMostGranule["group"] = rasterGroup["timestamp"]
                        centerMostGranule["index"] = idx

                    # Update the extent of the datacube
                    xmin = min(xmin, dsBounds[0])
                    ymin = min(ymin, dsBounds[1])
                    xmax = max(xmax, dsBounds[2])
                    ymax = max(ymax, dsBounds[3])
                except Exception as e:
                    api.logger.error(e)
                    return f"Error when building the ZARR for {rasterFile}", \
                           500
            offset += len(rasterGroup["rasters"])

        api.logger.info("Building datacube from the ZARRs")
        # If there is more than one file requested
        if not (len(rasterGroups) == 1 and
                len(rasterGroups[0]["rasters"]) == 1):
            try:
                # Generate a grid extending the center granule
                centerMostGranuleDS = groupedDatasets[
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

                dataCube = xr.concat(mergedDSPerBucket, dim="t")
            except Exception as e:
                api.logger.error(e)
                return "Error when merging the intermediary files", 500
        else:
            dataCube = groupedDatasets[list(groupedDatasets.keys())[0]][0]
        # TODO: merge manually dataset attributes

        api.logger.info("Writing datacube to Object Store")
        try:
            mapper = getMapperOutputObjectStore(api.payload["dataCubePath"])
            chunkSize = getChunkSize(dataCube.attrs['dtype'])
            dataCube.chunk({"x": chunkSize, "y": chunkSize, "t": 1}) \
                    .to_zarr(mapper, mode="w")
        except Exception as e:
            api.logger.error(e)
            return "Error when writing the ZARR to the object store", 500

        # Clean up the created zarrs
        if os.path.exists(zarrRootPath) and os.path.isdir(zarrRootPath):
            shutil.rmtree(zarrRootPath)

        return "Datacube built", 200
