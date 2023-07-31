from pydantic import BaseModel, Field

SOURCE_DESCRIPTION = "Designates where the product comes from. " + \
                     "For example, can be the satellite constellation " + \
                     "that took the original product (ie 'Sentinel2')."
FORMAT_DESCRIPTION = "Designates the transformation applied to the " + \
                     "raw product and the format of the final raster. " + \
                     "For example, 'L2A-SAFE'."
ALIAS_DESCRIPTION = "Name that aliases the desired product type, to " + \
                    "facilitate further references."


class RasterType(BaseModel):
    source: str = Field(description=SOURCE_DESCRIPTION)
    format: str = Field(description=FORMAT_DESCRIPTION)

    def __eq__(self, __o: object) -> bool:
        if type(__o) != RasterType:
            return False
        else:
            return self.format == __o.format and self.source == __o.source

    def to_key(self) -> str:
        """
        Returns a string version of the type to use as a key in a dictionary
        """
        return self.source + '-' + self.format


class AliasedRasterType(RasterType):
    alias: str = Field(description=ALIAS_DESCRIPTION)
