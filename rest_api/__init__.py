from flask_restx import Api

from .raster2zarr import api as R2Zapi

api = Api(title="ARLAS DataCube Builder API", version="1.0", description="An API to convert raster data to zarr archives",)

api.add_namespace(R2Zapi)