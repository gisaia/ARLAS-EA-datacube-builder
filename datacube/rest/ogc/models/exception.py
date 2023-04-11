from pydantic import BaseModel, Extra, Field


class Exception(BaseModel):
    class Config:
        extra = Extra.allow

    type: str
    title: str | None = Field(default=None)
    status: int | None = Field(default=None)
    detail: str | None = Field(default=None)
    instance: str | None = Field(default=None)
