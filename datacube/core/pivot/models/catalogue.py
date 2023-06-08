import enum

from pydantic import BaseModel, Field

from datacube.core.models.metadata import DatacubeMetadata


class DataType(str, enum.Enum):
    INT8 = "int8"
    INT16 = "int16"
    INT32 = "int32"
    INT64 = "int64"
    UINT8 = "uint8"
    UINT16 = "uint16"
    UINT32 = "uint32"
    UINT64 = "uint64"
    FLOAT16 = "float16"
    FLOAT32 = "float32"
    FLOAT64 = "float64"
    CINT16 = "cint16"
    CINT32 = "cint32"
    CFLOAT32 = "cfloat32"
    CFLOAT64 = "cfloat64"
    OTHER = "other"


class Band(BaseModel):
    data_type: DataType = Field()
    nodata: float | int = Field()


class Coordinates(BaseModel):
    __root__: list[float] = Field(min_items=2, max_items=2)


class Polygon(BaseModel):
    type: str = "Polygon"
    coordinates: list[Coordinates] = Field(min_items=4)


class Properties(DatacubeMetadata):
    # https://stac-extensions.github.io/projection/v1.0.0/schema.json
    epsg: int = Field(alias="proj:epsg")
    # https://stac-extensions.github.io/raster/v1.1.0/schema.json
    bands: list[Band] = Field(alias="raster:bands")


class CatalogueDescription(BaseModel):
    type: str = Field(default="Feature")
    stac_version: str = Field(default="1.0.0")
    stac_extensions: list[str] = Field(default=[
      "https://stac-extensions.github.io/projection/v1.0.0/schema.json",
      "https://stac-extensions.github.io/raster/v1.1.0/schema.json",
      "https://stac-extensions.github.io/datacube/v2.2.0/schema.json"])
    id: str = Field()
    collection: str = Field()
    bbox: list[float] = Field()
    geometry: Polygon = Field()
    properties: Properties = Field()
