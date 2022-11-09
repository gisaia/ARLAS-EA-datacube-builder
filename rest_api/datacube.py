#!/usr/bin/python3
from typing import List

import numpy as np
import xarray as xr
from flask_restx import Namespace, Resource
from shapely.geometry import Point

from models.rasterDrivers.fileFormats import FileFormats
from models.rasterDrivers.sentinel2_level2A import Sentinel2_Level2A
from models.request.datacube_build import DATACUBE_BUILD_REQUEST

from utils.geometry import bbox2polygon, completeGrid
from utils.objectStore import createInputObjectStore, \
                              getMapperOutputObjectStore
from utils.xarray import getBounds, getChunkSize, mergeDatasets

from urllib.parse import urlparse

api = Namespace("datacube",
                description="Build a data cube from raster files")

ZIP_EXTRACT_PATH = "tmp/"


@api.route('/build')
class DataCube_Build(Resource):

    @api.doc(params={
        'rasterFile': 'The raster files to build the data cube from',
        'dataCubePath': 'The Object Store path to the data cube',
        'roi': 'The Region Of Interest (bbox) to extract',
        'bands': 'The list of bands to extract',
        'targetResolution': 'The requested end resolution in meters',
        'tragetProjection': 'The targeted projection. Default :"EPSG:4326".'
        })
    @api.expect(DATACUBE_BUILD_REQUEST)
    def post(self):
        api.logger.info("[POST] /build")
        rasterFiles: List = api.payload["rasterFiles"]

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

                # Generate a grid extending the center granule
                lonStep = datasets[centermostGranuleDSindex].get("x") \
                                                            .diff("x").mean()
                latStep = datasets[centermostGranuleDSindex].get("y") \
                                                            .diff("y").mean()
                lon, lat = completeGrid(
                    datasets[centermostGranuleDSindex].get("x"), lonStep,
                    datasets[centermostGranuleDSindex].get("y"), latStep,
                    (xmin, ymin, xmax, ymax))

                # Starting with the centermost granule, merge datasets
                # TODO: group datasets by timestamp
                mergedDataset = datasets[centermostGranuleDSindex]
                for i in range(len(datasets)):
                    if i != centermostGranuleDSindex:
                        # Interpolate the granule with new grid on its extent
                        granuleBounds = getBounds(datasets[i])
                        granuleLon = lon[(lon[:] >= granuleBounds[0])
                                         & (lon[:] <= granuleBounds[2])]
                        granuleLat = lat[(lat[:] >= granuleBounds[1])
                                         & (lat[:] <= granuleBounds[3])]
                        granuleLon, granuleLat = completeGrid(
                            granuleLon, lonStep, granuleLat, latStep,
                            granuleBounds)

                        grid = xr.Dataset({"x": granuleLon, "y": granuleLat})
                        ds = datasets[i].interp_like(grid, method="nearest")

                        mergedDataset = mergeDatasets(mergedDataset, ds)
                # TODO: fuse merged granules along the time dimension
            except Exception as e:
                api.logger.error(e)
                return "Error when merging the intermediary files", 500
        else:
            mergedDataset = datasets[0]
        # TODO: merge manually dataset attributes

        api.logger.info("Writing datacube to Object Store")
        try:
            mapper = getMapperOutputObjectStore(api.payload["dataCubePath"])
            chunkSize = getChunkSize(mergedDataset.attrs['dtype'])
            mergedDataset.chunk({"x": chunkSize, "y": chunkSize, "t": 1}) \
                         .to_zarr(mapper, mode="w")
        except Exception as e:
            api.logger.error(e)
            return "Error when writing the ZARR to the object store", 500

        return "Operation completed", 200
