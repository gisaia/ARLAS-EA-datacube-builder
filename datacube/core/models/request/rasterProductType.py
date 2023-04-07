from typing import Annotated
from fastapi import Query
from pydantic import BaseModel

SOURCE_DESCRIPTION = "The source of the raster product."
FORMAT_DESCRIPTION = "The format of the raster product."
ALIAS_DESCRIPTION = "The alias of the raster product."


class RasterType(BaseModel):
    source: Annotated[str, Query(description=SOURCE_DESCRIPTION)]
    format: Annotated[str, Query(description=FORMAT_DESCRIPTION)]

    def __eq__(self, __o: object) -> bool:
        if type(__o) != RasterType:
            return False
        else:
            return self.format == __o.format and self.source == __o.source


class AliasedRasterType(RasterType):
    alias: Annotated[str, Query(description=ALIAS_DESCRIPTION)]
