from flask_restx import Api

from .datacube import api as DataCubeAPI

api = Api(title="ARLAS DataCube Builder API",
          version="1.0",
          description="An API to build data cubes from raster files")

api.add_namespace(DataCubeAPI)
