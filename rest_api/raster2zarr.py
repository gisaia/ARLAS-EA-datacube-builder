#!/usr/bin/python3

import re
from datetime import datetime
from zipfile import ZipFile

from dateutil import parser
from flask_restx import Namespace, Resource, fields
from lxml import etree

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

ZIP_EXTRACT_PATH = "tmp/"
PRODUCT_START_TIME = "n1:General_Info/Product_Info/PRODUCT_START_TIME"
PRODUCT_STOP_TIME = "n1:General_Info/Product_Info/PRODUCT_STOP_TIME"


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
            # Extract timestamp of production of the product
            for fileName in listOfFileNames:
                if re.match(r".*MTD_MSI.*\.xml", fileName):
                    zipObj.extract(fileName, ZIP_EXTRACT_PATH)
                    metadata: etree._ElementTree = etree.parse(
                        ZIP_EXTRACT_PATH + fileName)
                    root: etree._Element = metadata.getroot()
                    startTime = parser.parse(root.xpath(
                        PRODUCT_START_TIME, namespaces=root.nsmap)[0].text)

                    stopTime = parser.parse(root.xpath(
                        PRODUCT_STOP_TIME, namespaces=root.nsmap)[0].text)

                    productTime = int((datetime.timestamp(startTime)
                                       + datetime.timestamp(stopTime)) / 2)

            for band in api.payload["bands"]:
                for fileName in listOfFileNames:
                    if re.match(r".*/IMG_DATA/.*" + band + r"\.jp2", fileName):
                        zipObj.extract(fileName, ZIP_EXTRACT_PATH)
                        bandsToExtract.append(ZIP_EXTRACT_PATH + fileName)

        try:
            polygon = bbox2polygon(api.payload["roi"])
            convert(bandsToExtract, api.payload["zarrFile"],
                    productTime, polygon=polygon)
            return "Operation completed", 200
        except Exception:
            return "Error in the process", 500
