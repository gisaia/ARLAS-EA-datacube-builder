#!/usr/bin/python3
from typing import List

import xarray as xr
from flask_restx import Namespace, Resource, fields

from models.rasterDrivers.fileFormats import FileFormats
from models.rasterDrivers.sentinel2_level2A import Sentinel2_Level2A
from models.request.rasterFile import RASTERFILE_MODEL

from utils.geometry import bbox2polygon
from utils.objectStore import createInputObjectStore

from urllib.parse import urlparse

api = Namespace("raster2zarr",
                description="Transform a raster file into a zarr file")

CONVERTRASTER_MODEL = api.model(
    "ConvertRaster",
    {
        "rasterFiles": fields.List(
            fields.Nested(RASTERFILE_MODEL),
            required=True,
            readonly=True),
        "zarrFile": fields.String(
            required=True,
            readonly=True,
            description="The path of the output ZARR file"),
        "roi": fields.String(
            readonly=True,
            description="The BBox to extract"),
        "bands": fields.List(
            fields.String,
            readonly=True,
            description="The list of bands to extract"),
        "targetResolution": fields.Integer(
            readonly=True,
            description="The requested end resolution in meters"
        )
    }
)

ZIP_EXTRACT_PATH = "tmp/"
PRODUCT_START_TIME = "n1:General_Info/Product_Info/PRODUCT_START_TIME"
PRODUCT_STOP_TIME = "n1:General_Info/Product_Info/PRODUCT_STOP_TIME"


@api.route('/convert')
class ConvertRaster(Resource):

    @api.doc(params={
        'rasterFile': 'The raster files to transform (Sentinel-2 zip)',
        'zarrFile': 'The output of the transformation',
        'roi': 'The Region Of Interest (bbox) to extract',
        'bands': 'The list of bands to extract',
        'targetResolution': 'The requested end resolution in meters'
        })
    @api.expect(CONVERTRASTER_MODEL)
    def post(self):
        api.logger.info("[POST] /convert")
        rasterFiles: List = api.payload["rasterFiles"]

        polygon = bbox2polygon(api.payload["roi"]) \
            if "roi" in api.payload \
            else None

        targetResolution = api.payload["targetResolution"] \
            if "targetResolution" in api.payload \
            else 10

        datasets: List[xr.Dataset] = []

        for idx, rasterFile in enumerate(rasterFiles):
            api.logger.info(f"[File {idx + 1}] Extracting bands of interest")
            inputObjectStore = createInputObjectStore(
                    urlparse(rasterFile["rasterPath"]).scheme)

            if rasterFile["rasterFormat"] == FileFormats.SENTINEL2_2A.value:

                rasterArchive = Sentinel2_Level2A(inputObjectStore,
                                                  rasterFile["rasterPath"],
                                                  api.payload["bands"],
                                                  targetResolution)
            else:
                return f"'{rasterFile['rasterFormat']}' not accepted", 500

            try:
                api.logger.info(f"[File {idx + 1}] Building ZARR from bands")
                dataset = rasterArchive.convert(
                    api.payload["zarrFile"] + f"_{idx}", polygon=polygon)
                datasets.append(dataset)
            except Exception as e:
                api.logger.error(e)
                return f"Error when generating the ZARR for {rasterFile}", 500

        api.logger.info("Building datacube from the ZARRs")
        if len(datasets) != 1:
            try:
                xr.combine_by_coords(datasets) \
                    .to_zarr(api.payload["zarrFile"], mode="w")
            except Exception as e:
                api.logger.error(e)
                return "Error when merging the intermediary files", 500
        else:
            datasets[0].to_zarr(api.payload["zarrFile"], mode="w")

        return "Operation completed", 200
