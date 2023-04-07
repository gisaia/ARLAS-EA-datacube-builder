from __future__ import annotations
from pydantic import BaseModel, Field, Extra
from typing import Any

from datacube.rest.ogc.models.enums import ObjectType


class Reference(BaseModel):
    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True

    _ref: str = Field(..., alias="$ref")


class SchemaItem(BaseModel):
    class Config:
        extra = Extra.forbid

    title: str | None = Field(default=None)
    multipleOf: float | None = Field(ge=0)
    maximum: float | None = Field(default=None)
    exclusiveMaximum: bool | None = Field(default=False)
    minimum: float | None = Field(default=None)
    exclusiveMinimum: bool | None = Field(default=False)
    maxLength: int | None = Field(ge=0)
    minLength: int | None = Field(ge=0)
    pattern: str | None = Field(default=None)
    maxItems: int | None = Field(ge=0)
    minItems: int | None = Field(ge=0)
    uniqueItems: bool | None = Field(default=False)
    maxProperties: int | None = Field(ge=0)
    minProperties: int | None = Field(ge=0)
    required: list[str] | None = Field(None, min_items=1)
    enum: list[Any] | None = Field(None, min_items=1)
    type: ObjectType | None = Field(default=None)
    not_: Reference | SchemaItem | None = Field(default=None, alias="not")
    allOf: list[Reference | SchemaItem] | None = Field(default=None)
    oneOf: list[Reference | SchemaItem] | None = Field(default=None)
    anyOf: list[Reference | SchemaItem] | None = Field(default=None)
    items: Reference | SchemaItem | None = Field(default=None)
    properties: dict[str, Reference | SchemaItem] | None = Field(default=None)
    additionalProperties: Reference | SchemaItem | bool | None \
        = Field(default=None)
    description: str | None = Field(default=None)
    format: str | None = Field(default=None)
    default: Any | None = Field(default=None)
    nullable: bool | None = Field(default=False)
    readOnly: bool | None = Field(default=False)
    writeOnly: bool | None = Field(default=False)
    example: Any | None = Field(default=None)
    deprecated: bool | None = Field(default=False)
    contentMediaType: str | None = Field(default=None)
    contentEncoding: str | None = Field(default=None)
    contentSchema: str | None = Field(default=None)
