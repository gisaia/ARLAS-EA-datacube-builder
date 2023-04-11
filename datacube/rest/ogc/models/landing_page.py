from pydantic import BaseModel, Field

from datacube.rest.ogc.models.link import Link


class LandingPage(BaseModel):
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    links: list[Link]
