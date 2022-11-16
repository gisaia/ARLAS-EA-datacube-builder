#!/usr/bin/python3
from typing import List

import numpy as np
import xarray as xr
from flask_restx import Namespace, Resource
from shapely.geometry import Point

from models.rasterDrivers.fileFormats import FileFormats
from models.rasterDrivers.sentinel2_level2A import Sentinel2_Level2A
from models.request.datacube_build import DATACUBE_BUILD_REQUEST
from models.request.rasterFile import RASTERFILE_MODEL

from utils.geometry import bbox2polygon, completeGrid
from utils.objectStore import createInputObjectStore, \
                              getMapperOutputObjectStore
from utils.xarray import getBounds, getChunkSize, mergeDatasets

from urllib.parse import urlparse

api = Namespace("cube",
                description="Build a data cube from raster files")
api.models[DATACUBE_BUILD_REQUEST.name] = DATACUBE_BUILD_REQUEST
api.models[RASTERFILE_MODEL.name] = RASTERFILE_MODEL

ZIP_EXTRACT_PATH = "tmp/"


@api.route('/build')
class DataCube_Build(Resource):

    @api.expect(DATACUBE_BUILD_REQUEST)
    def post(self):
        api.logger.info("[POST] /build")
        rasterFiles: List = api.payload["rasterCompositions"]

        roi = bbox2polygon(api.payload["roi"]) \
            if "roi" in api.payload \
            else None

        targetResolution = api.payload["targetResolution"] \
            if "targetResolution" in api.payload \
            else 10

        targetProjection = api.payload["tragetProjection"] \
            if "tragetProjection" in api.payload \
            else "EPSG:4326"

        parsedDestination = urlparse(api.payload["dataCubePath"])

        datasets: List[xr.Dataset] = []

        for idx, rasterFile in enumerate(rasterFiles):
            api.logger.info(f"[File {idx + 1}] Extracting bands of interest")
            inputObjectStore = createInputObjectStore(
                    urlparse(rasterFile["rasterPath"]).scheme)

            try:
                if rasterFile["rasterFormat"] == FileFormats.SENTINEL2_2A.value:
                    rasterArchive = Sentinel2_Level2A(
                        inputObjectStore, rasterFile["rasterPath"],
                        api.payload["bands"], targetResolution,
                        rasterFile["rasterTimestamp"])
                else:
                    return f"'{rasterFile['rasterFormat']}' not accepted", 500
            except Exception as e:
                api.logger.error(e)
                return f"Error when extracting the bands for {rasterFile}", 500

            try:
                api.logger.info(f"[File {idx + 1}] Building ZARR from bands")

                dataset = rasterArchive.buildZarr(
                  f"{parsedDestination.netloc}/{parsedDestination.path}_{idx}",
                  targetProjection, polygon=roi)
                datasets.append(dataset)
            except Exception as e:
                api.logger.error(e)
                return f"Error when generating the ZARR for {rasterFile}", 500

        api.logger.info("Building datacube from the ZARRs")
        if len(datasets) != 1:
            try:
                # Group the datasets by timestamp to merge them
                temporalBuckets: dict[float, List] = {}
                # Find the centermost granule based on ROI and maximum bounds
                xmin, ymin, xmax, ymax = np.inf, np.inf, -np.inf, -np.inf
                roiCentroid: Point = roi.centroid
                centermostGranuleDSindex = 0
                minDistance = np.inf
                for i, ds in enumerate(datasets):
                    dsBounds = getBounds(ds)
                    granuleCenter = Point((dsBounds[0] + dsBounds[2])/2,
                                          (dsBounds[1] + dsBounds[3])/2)
                    if roiCentroid.distance(granuleCenter) < minDistance:
                        minDistance = roiCentroid.distance(granuleCenter)
                        centermostGranuleDSindex = i
                    xmin = min(xmin, dsBounds[0])
                    ymin = min(ymin, dsBounds[1])
                    xmax = max(xmax, dsBounds[2])
                    ymax = max(ymax, dsBounds[3])

                    # Add dataset to a temporal bucket
                    if ds.get("t").values[0] in temporalBuckets.keys():
                        temporalBuckets[ds.get("t").values[0]].append(ds)
                    else:
                        temporalBuckets[ds.get("t").values[0]] = [ds]

                # Generate a grid extending the center granule
                lonStep = datasets[centermostGranuleDSindex].get("x") \
                                                            .diff("x").mean()
                latStep = datasets[centermostGranuleDSindex].get("y") \
                                                            .diff("y").mean()
                lon, lat = completeGrid(
                    datasets[centermostGranuleDSindex].get("x"), lonStep,
                    datasets[centermostGranuleDSindex].get("y"), latStep,
                    (xmin, ymin, xmax, ymax))

                # For each time bucket, create a mosaick of the datasets
                timestamps = list(temporalBuckets.keys())
                timestamps.sort()

                mergedDSPerBucket = []
                for t in timestamps:
                    mergedDataset = None
                    for dataset in temporalBuckets[t]:
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
            dataCube = datasets[0]
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

        return "Datacube built", 200
