from flask_restx import Model, fields

from .rasterFile import RASTERFILE_MODEL, RasterFile
from utils.flaskFields import DictItem

RASTERGROUP_MODEL = Model(
    "RasterGroup",
    {
        "rasters": fields.List(
            fields.Nested(RASTERFILE_MODEL),
            required=True,
            readonly=True,
            description="The list of raster files in this group."
        ),
        "timestamp": fields.Integer(
            required=True,
            readonly=True,
            description="The timestamp of this temporal group."
        ),
        "metadata": DictItem(
            required=False,
            readonly=True,
            description="Optional metadata for this group."
        )
    }
)


class RasterGroup:

    def __init__(self, rasters, timestamp: int, metadata=None):
        self.rasters = [RasterFile(**raster) for raster in rasters]
        self.timestamp = timestamp
        self.metadata = metadata

    def __repr__(self):
        return str(self.as_dict())

    def as_dict(self):
        rasterGroup = {}
        rasterGroup["rasters"] = [raster.as_dict() for raster in self.rasters]
        rasterGroup["timestamp"] = self.timestamp
        if self.metadata:
            rasterGroup["metadata"] = self.metadata

        return rasterGroup
