from typing import Any

from pydantic import BaseModel, Field

from datacube.core.models.request.rasterGroup import RasterGroup


class Dimension(BaseModel):
    axis: str = Field()
    description: str = Field()


class HorizontalSpatialDimension(Dimension):
    extent: list[float | int] = Field()
    step: float | int | None = Field(default=None)
    type: str = Field(default="spatial")
    reference_system: str | int | Any = Field(default=4326)


class TemporalDimension(Dimension):
    extent: list[str | None] = Field()
    step: str | None = Field()


class Variable(BaseModel):
    dimensions: list[str] = Field()
    type: str = Field()
    description: str = Field()
    extent: list[float | int | str | None] = Field()
    unit: str = Field()
    expression: str = Field()


class QualityIndicators(BaseModel):
    time_compacity: float = Field()
    spatial_coverage: float = Field()
    group_lightness: float = Field()


class QualityIndicatorsCube(QualityIndicators):
    time_regularity: float = Field()


class DatacubeMetadata(BaseModel):
    dimensions: dict[str, Dimension] = Field()
    variables: dict[str, Variable] = Field()
    composition: list[RasterGroup] = Field()
    preview: dict[str, str] = Field()
    number_of_chunks: int = Field()
    chunk_weight: int = Field()
    quality_indicators: QualityIndicatorsCube = Field()
