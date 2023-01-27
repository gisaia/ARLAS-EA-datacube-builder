from flask_restx import Model, fields

RASTERPRODUCTTYPE_MODEL = Model(
    "RasterProductType",
    {
        "format": fields.String(
            required=True,
            readonly=True,
            description="The format of the raster product.",
            enum=["2A-Theia", "2A-Safe"]
        ),
        "source": fields.String(
            required=True,
            readonly=True,
            description="The source of the raster product.",
            enum=["Sentinel2"]
        )
    }
)


class RasterProductType:

    def __init__(self, source, format):
        self.source: str = source
        self.format: str = format

    def __repr__(self):
        return str(self.as_dict())

    def as_dict(self):
        rasterProductType = {}
        rasterProductType["path"] = self.source
        rasterProductType["type"] = self.format

        return rasterProductType

    def __eq__(self, __o: object) -> bool:
        if type(__o) != RasterProductType:
            return False
        else:
            return self.format == __o.format and self.source == __o.source
