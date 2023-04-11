from pydantic import BaseModel, Field

DC_URL_DESCRIPTION = "URL at which the datacube is created"
PREVIEW_URL_DESCRIPTION = "URL at which the datacube's preview is created"
PREVIEW_DESCRIPTION = "The preview of the datacube encoded in base64"


class CubeBuildResult(BaseModel):
    datacube_url: str = Field(description=DC_URL_DESCRIPTION)
    preview_url: str = Field(description=PREVIEW_URL_DESCRIPTION)
    preview: str = Field(description=PREVIEW_DESCRIPTION)
