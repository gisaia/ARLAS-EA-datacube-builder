from typing import Any

from pydantic import BaseModel, Field


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


class DatacubeMetadata(BaseModel):
    dimensions: dict[str, Dimension] = Field()
    variables: dict[str, Variable] = Field()
    composition: dict[int, list[str]] = Field()
    preview: dict[str, str] = Field()
