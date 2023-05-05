from pydantic import BaseModel, Field

from datacube.rest.server.models.dc3_builder import DC3BuilderConfiguration
from datacube.rest.server.models.hazelcast import HazelcastConfiguration


class ServerConfigurationModel(BaseModel):
    dc3_builder: DC3BuilderConfiguration = Field(
        description="Configuration for the server", alias="dc3-builder")
    hazelcast: HazelcastConfiguration | None = Field(
        description="Configuration for the Hazelcast cache. " +
                    "Is optional when starting the server locally")
