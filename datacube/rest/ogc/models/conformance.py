from pydantic import BaseModel


class Conforms(BaseModel):
    conformsTo: list[str]
