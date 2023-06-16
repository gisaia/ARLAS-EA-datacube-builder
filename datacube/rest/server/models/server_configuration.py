from pydantic import BaseModel, Field

from datacube.rest.server.models.dc3_builder import DC3BuilderConfiguration


class ServerConfigurationModel(BaseModel):
    dc3_builder: DC3BuilderConfiguration = Field(
        description="Configuration for the server", alias="dc3-builder")
