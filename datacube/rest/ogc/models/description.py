from typing import Any

from pydantic import BaseModel, Field

from datacube.rest.ogc.models.enums import MaxOccur
from datacube.rest.ogc.models.schema import Reference, SchemaItem


class Metadata(BaseModel):
    title: str | None = Field(default=None)
    role: str | None = Field(default=None)
    href: str | None = Field(default=None)


class AdditionalParameter(BaseModel):
    name: str
    value: list[str | float | int | list[Any], dict[str, Any]]


class AdditionalParameters(Metadata):
    parameters: list[AdditionalParameter] | None = Field(default=None)


class DescriptionType(BaseModel):
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    keywords: list[str] | None = Field(default=None)
    metadata: list[Metadata] | None = Field(default=None)
    additionalParameters: AdditionalParameters | None = Field(default=None)


class InputDescription(DescriptionType):
    class Config:
        allow_population_by_field_name = True

    minOccurs: int | None = 1
    maxOccurs: int | MaxOccur | None = None
    schema_: Reference | SchemaItem = Field(..., alias="schema")


class OutputDescription(DescriptionType):
    class Config:
        allow_population_by_field_name = True

    schema_: Reference | SchemaItem = Field(..., alias="schema")
