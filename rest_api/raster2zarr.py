#!/usr/bin/python3

from flask import Flask
from flask_restx import Namespace, Resource, fields

from utils import convert

from pprint import pprint

api = Namespace("raster2zarr", description="Transform a raster file into a zarr file")

RASTER_FILE = "./data/soilClassificationwithMachineLearningwithPythonScikitLearn/S2B_MSIL1C_20200917T151709_N0209_R125_T18LUM_20200917T203629.SAFE/GRANULE/L1C_T18LUM_A018455_20200917T151745/IMG_DATA/T18LUM_20200917T151709_B01.jp2"
ZARR_FILE = "./output/zarr/test"

CONVERTRASTER_MODEL = api.model(
    "ConvertRaster",
    {
        "rasterFile": fields.String(
            required=True, 
            readonly=True, 
            description="The path to the raster file to convert"),
        "zarrFile": fields.String(
            readonly=True, 
            description="The path of the output ZARR file")
    }
)

@api.route('/convert')
class ConvertRaster(Resource):

    @api.doc(params={
        'rasterFile': 'The raster file to transform',
        'zarrFile': 'The output of the transformation'
        })
    @api.expect(CONVERTRASTER_MODEL)
    def post(self):
        pprint("[CONVERT RASTER] Received POST")
        try:
            convert(api.payload["rasterFile"], api.payload["zarrFile"])
            return "Operation completed", 200
        except:
            return "Error in the process", 500
        
