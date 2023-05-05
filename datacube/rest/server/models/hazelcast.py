from pydantic import BaseModel, Field


class HazelcastConfiguration(BaseModel):
    host: str = Field(description="Host machine adress of " +
                      "the Hazelcast docker container")
