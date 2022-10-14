#!/usr/bin/python3

import re
from zipfile import ZipFile

from flask_restx import Namespace, Resource, fields

from utils.geometry import bbox2polygon
from utils.raster2zarr import convert

api = Namespace("raster2zarr",
                description="Transform a raster file into a zarr file")

CONVERTRASTER_MODEL = api.model(
    "ConvertRaster",
    {
        "rasterFile": fields.String(
            required=True,
            readonly=True,
            description="The path to the raster file to convert"),
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
            description="The list of bands to extract")
    }
)

ZIP_EXTRACT_PATH = "tmp"


@api.route('/convert')
class ConvertRaster(Resource):

    @api.doc(params={
        'rasterFile': 'The raster file to transform (Sentinel-2 zip)',
        'zarrFile': 'The output of the transformation',
        'roi': 'The Region Of Interest (bbox) to extract',
        'bands': 'The list of bands to extract'
        })
    @api.expect(CONVERTRASTER_MODEL)
    def post(self):
        rasterFile = api.payload["rasterFile"]

        if rasterFile[-4:] != ".zip":
            return "Wrong file format", 500

        bandsToExtract = []
        with ZipFile(rasterFile, "r") as zipObj:
            listOfFileNames = zipObj.namelist()
            for band in api.payload["bands"]:
                for fileName in listOfFileNames:
                    if re.match(".*/IMG_DATA/.*" + band + "\.jp2", fileName):
                        zipObj.extract(fileName, ZIP_EXTRACT_PATH)
                        bandsToExtract.append(
                            ZIP_EXTRACT_PATH + "/" + fileName)

        try:
            polygon = bbox2polygon(api.payload["roi"])
            convert(bandsToExtract, api.payload["zarrFile"], polygon=polygon)
            return "Operation completed", 200
        except Exception:
            return "Error in the process", 500
