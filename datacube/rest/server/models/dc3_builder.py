from pydantic import BaseModel, Field


class DC3BuilderConfiguration(BaseModel):
    host: str = Field(description="Host adress for the service")
    port: int | str = Field(description="Port of the server")
    debug: bool | None = Field(description="Whether the app is launched" +
                               "in debug mode")
