from pydantic import Field, BaseModel
import fastapi


class RESTException(BaseModel):
    type: str
    status_code: int
    title: str | None = Field(default=None)
    detail: str | None = Field(default=None)
    instance: str | None = Field(default=None)
    traceback: str | None = Field(default=None)
