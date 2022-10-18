#!/usr/bin/python3

from typing import List

import xarray as xr
from flask_restx import Namespace, Resource, fields

from utils.drivers.fileFormats import FileFormats
from utils.drivers.sentinel2_level2A import Sentinel2_Level2A
from utils.geometry import bbox2polygon

api = Namespace("raster2zarr",
                description="Transform a raster file into a zarr file")

CONVERTRASTER_MODEL = api.model(
    "ConvertRaster",
    {
        "rasterFile": fields.List(
            fields.String,
            required=True,
            readonly=True,
            description="The path to the raster files to convert \
                        in the format TYPE_OF_FILE:PATH"),
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
        'rasterFile': 'The raster files to transform (Sentinel-2 zip) \
            in the format TYPE_OF_FILE:PATH',
        'zarrFile': 'The output of the transformation',
        'roi': 'The Region Of Interest (bbox) to extract',
        'bands': 'The list of bands to extract',
        'targetResolution': 'The requested end resolution in meters'
        })
    @api.expect(CONVERTRASTER_MODEL)
    def post(self):
        rasterFiles: List[str] = api.payload["rasterFile"]

        polygon = bbox2polygon(api.payload["roi"]) \
            if "roi" in api.payload \
            else None

        targetResolution = api.payload["targetResolution"] \
            if "targetResolution" in api.payload \
            else 10

        datasets = []

        for idx, rasterFile in enumerate(rasterFiles):
            try:
                fileFormat, rasterPath = rasterFile.split(":", maxsplit=1)
            except ValueError:
                return "'rasterFile' should be a list of TYPE_OF_FILE:PATH", \
                        500

            if fileFormat == FileFormats.SENTINEL2_2A.value:
                rasterArchive = Sentinel2_Level2A(rasterPath,
                                                  api.payload["bands"],
                                                  targetResolution)
            else:
                return f"'{fileFormat}' format not accepted", 500

            try:
                dataset = rasterArchive.convert(
                    api.payload["zarrFile"] + f"_{idx}", polygon=polygon)
                datasets.append(dataset)
            except Exception:
                return f"Error when generating the ZARR for {rasterFile}", 500

        if len(datasets) != 1:
            print("Combining datasets")
            try:
                xr.combine_by_coords(datasets) \
                    .to_zarr(api.payload["zarrFile"], mode="w")
            except Exception:
                return "Error when merging the intermediary files", 500

        return "Operation completed", 200
