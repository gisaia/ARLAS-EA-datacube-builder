from pydantic import BaseModel, Field

PRODUCT_URL_DESCRIPTION = \
    "URL at which the product (datacube or pivot archive) is created"
PREVIEW_URL_DESCRIPTION = "URL at which the datacube's preview is created."
PREVIEW_DESCRIPTION = "The preview of the datacube encoded in base64"


class CubeBuildResult(BaseModel):
    product_url: str = Field(description=PRODUCT_URL_DESCRIPTION)
    preview_url: str = Field(description=PREVIEW_URL_DESCRIPTION)
    preview: str = Field(description=PREVIEW_DESCRIPTION)
