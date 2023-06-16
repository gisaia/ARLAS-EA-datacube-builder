import enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

from datacube.core.models.request.rasterGroup import RasterGroup


class DimensionType(str, enum.Enum):
    SPATIAL = "spatial"
    TEMPORAL = "temporal"


class HorizontalSpatialDimension(BaseModel):
    axis: str = Field()
    description: str = Field()
    type: Literal[DimensionType.SPATIAL]
    extent: list[float | int] = Field()
    step: float | int | None = Field(default=None)
    reference_system: str | int | Any = Field(default=4326)


class TemporalDimension(BaseModel):
    axis: str = Field()
    description: str = Field()
    type: Literal[DimensionType.TEMPORAL]
    extent: list[str | None] = Field()
    step: str | None = Field()


Dimension = Annotated[HorizontalSpatialDimension | TemporalDimension,
                      Field(discriminator="type")]


class Variable(BaseModel):
    dimensions: list[str] = Field()
    type: str = Field()
    description: str | None = Field()
    extent: list[float | int | str] = Field()
    unit: str | None = Field()
    expression: str = Field()


class QualityIndicators(BaseModel):
    time_compacity: float = Field()
    spatial_coverage: float = Field()
    group_lightness: float = Field()


class QualityIndicatorsCube(QualityIndicators):
    time_regularity: float = Field()


class DatacubeMetadata(BaseModel):
    dimensions: dict[str, Dimension] = Field(alias="cube:dimensions")
    variables: dict[str, Variable] = Field(alias="cube:variables")
    composition: list[RasterGroup] = Field(alias="dc3:composition")
    preview: dict[str, str] = Field(alias="dc3:preview")
    number_of_chunks: int = Field(alias="dc3:number_of_chunks")
    chunk_weight: int = Field(alias="dc3:chunk_weight")
    quality_indicators: QualityIndicatorsCube \
        = Field(alias="dc3:quality_indicators")
    fill_ratio: float = Field(alias="dc3:fill_ratio")
    description: str | None = Field(alias="dc3:description")
