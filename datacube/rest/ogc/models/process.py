from pydantic import BaseModel, Field
from typing import Callable

from datacube.rest.ogc.models.description import (DescriptionType,
                                                  InputDescription,
                                                  OutputDescription)
from datacube.rest.ogc.models.enums import JobControlOptions, TransmissionMode
from datacube.rest.ogc.models.link import Link


class ProcessSummary(DescriptionType):
    id: str
    version: str
    jobControlOptions: list[JobControlOptions] | None = Field(default=None)
    outputTransmission: list[TransmissionMode] | None = Field(default=None)
    links: list[Link] | None = Field(default=None)


class ProcessList(BaseModel):
    processes: list[ProcessSummary]
    links: list[Link] | None = Field(default=None)


class ProcessDescription(ProcessSummary):
    inputs: dict[str, InputDescription] | None = Field(default=None)
    outputs: dict[str, OutputDescription] | None = Field(default=None)


class ProcessListItem(BaseModel):
    process: ProcessDescription
    method: Callable
