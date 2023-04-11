from pydantic import BaseModel, Field

SOURCE_DESCRIPTION = "The source of the raster product."
FORMAT_DESCRIPTION = "The format of the raster product."
ALIAS_DESCRIPTION = "The alias of the raster product."


class RasterType(BaseModel):
    source: str = Field(description=SOURCE_DESCRIPTION)
    format: str = Field(description=FORMAT_DESCRIPTION)

    def __eq__(self, __o: object) -> bool:
        if type(__o) != RasterType:
            return False
        else:
            return self.format == __o.format and self.source == __o.source


class AliasedRasterType(RasterType):
    alias: str = Field(description=ALIAS_DESCRIPTION)
