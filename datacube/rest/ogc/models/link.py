from pydantic import BaseModel, Field


class Link(BaseModel):
    href: str
    rel: str | None = Field(default=None)
    type: str | None = Field(default=None)
    hreflang: str | None = Field(default=None)
    title: str | None = Field(default=None)
