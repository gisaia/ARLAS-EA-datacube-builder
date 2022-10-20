#!/usr/bin/python3
import logging
from typing import List

import xarray as xr
from flask_restx import Namespace, Resource, fields

from models.drivers.fileFormats import FileFormats
from models.drivers.sentinel2_level2A import Sentinel2_Level2A
from utils.geometry import bbox2polygon
from models.request.rasterFile import RASTERFILE_MODEL

api = Namespace("raster2zarr",
                description="Transform a raster file into a zarr file")

logging.basicConfig(level=logging.INFO)

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
        rasterFiles: List = api.payload["rasterFiles"]

        polygon = bbox2polygon(api.payload["roi"]) \
            if "roi" in api.payload \
            else None

        targetResolution = api.payload["targetResolution"] \
            if "targetResolution" in api.payload \
            else 10

        datasets = []

        for idx, rasterFile in enumerate(rasterFiles):
            if rasterFile["rasterFormat"] == FileFormats.SENTINEL2_2A.value:
                rasterArchive = Sentinel2_Level2A(rasterFile["rasterPath"],
                                                  api.payload["bands"],
                                                  targetResolution)
            else:
                return f"'{rasterFile['rasterFormat']}' not accepted", 500

            try:
                dataset = rasterArchive.convert(
                    api.payload["zarrFile"] + f"_{idx}", polygon=polygon,
                    logger=api.logger)
                datasets.append(dataset)
            except Exception:
                return f"Error when generating the ZARR for {rasterFile}", 500

        if len(datasets) != 1:
            api.logger.info("Combining datasets")
            try:
                xr.combine_by_coords(datasets) \
                    .to_zarr(api.payload["zarrFile"], mode="w")
            except Exception:
                return "Error when merging the intermediary files", 500

        return "Operation completed", 200
