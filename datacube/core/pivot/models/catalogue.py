import enum

from pydantic import BaseModel, Field
from datacube.core.models.enums import SensorFamily

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


# Not really compliant with STAC extension as not nan nodata values
# will be coerced to string, but no fix available until v2 is released
# according to https://github.com/pydantic/pydantic/issues/1779
class Band(BaseModel):
    data_type: DataType = Field()
    nodata: str = Field()


class Coordinates(BaseModel):
    __root__: list[float] = Field(min_items=2, max_items=2)


class Polygon(BaseModel):
    type: str = "Polygon"
    coordinates: list[Coordinates] = Field(min_items=4)


class Properties(DatacubeMetadata):
    datetime: str = Field(description="Date time of the product (ISO 8601)")
    start_datetime: str = Field()
    end_datetime: str = Field()

    # https://stac-extensions.github.io/processing/v1.1.0/schema.json
    level: str = Field(default="DATACUBE", alias="processing:level")

    # Domino-X
    imageFileFormat: str = Field(default="ZARR", alias="dox:imageFileFormat")
    thematics: list[str] | None = Field(alias="dox:thematics")
    sensorFamily: SensorFamily = Field(alias="dox:sensorFamily")

    # Add when coarsing is present
    # gsd: float | int = Field()
    # https://stac-extensions.github.io/projection/v1.0.0/schema.json
    epsg: int = Field(alias="proj:epsg")

    # https://stac-extensions.github.io/raster/v1.1.0/schema.json
    bands: list[Band] = Field(alias="raster:bands")


class CatalogueDescription(BaseModel):
    title: str = Field()
    description: str | None = Field()
    type: str = Field(default="Feature")
    stac_version: str = Field(default="1.0.0")
    stac_extensions: list[str] = Field(default=[
      "https://stac-extensions.github.io/projection/v1.0.0/schema.json",
      "https://stac-extensions.github.io/raster/v1.1.0/schema.json",
      "https://stac-extensions.github.io/datacube/v2.2.0/schema.json",
      "https://stac-extensions.github.io/processing/v1.1.0/schema.json",
      "https://dox/stac-extensions/dox/v1.0.0/schema.json",
      "https://dox/stac-extensions/dox_dc3/v1.0.0/schema.json"])
    id: str = Field()
    bbox: list[float] = Field()
    geometry: Polygon = Field()
    properties: Properties = Field()
