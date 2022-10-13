#!/usr/bin/python3

from flask_restx import Namespace, Resource, fields

from utils import convert, bbox2polygon

api = Namespace("raster2zarr", description="Transform a raster file into a zarr file")

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
            description="The BBox to extract")
    }
)

@api.route('/convert')
class ConvertRaster(Resource):

    @api.doc(params={
        'rasterFile': 'The raster file to transform',
        'zarrFile': 'The output of the transformation',
        'roi': 'The Region Of Interest (bbox) to extract'
        })
    @api.expect(CONVERTRASTER_MODEL)
    def post(self):
        try:
            polygon = bbox2polygon(api.payload["roi"])
            convert(api.payload["rasterFile"], api.payload["zarrFile"], polygon=polygon)
            return "Operation completed", 200
        except:
            return "Error in the process", 500
        
