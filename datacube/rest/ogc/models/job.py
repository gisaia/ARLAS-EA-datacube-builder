import datetime

from pydantic import BaseModel, Extra, Field

from datacube.rest.ogc.models.enums import JobType, StatusCode
from datacube.rest.ogc.models.link import Link


class StatusInfo(BaseModel):
    class Config:
        extra = Extra.allow

    processID: str | None = Field(default=None)
    type: JobType
    jobID: str
    status: StatusCode
    message: str | None = Field(default=None)
    created: datetime.datetime | None = Field(default=None)
    started: datetime.datetime | None = Field(default=None)
    finished: datetime.datetime | None = Field(default=None)
    updated: datetime.datetime | None = Field(default=None)
    progress: int | None = Field(default=None, ge=0, le=100)
    links: list[Link] | None = Field(default=None)
