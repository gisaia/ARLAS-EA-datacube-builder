from matplotlib import cm
from pydantic import BaseModel, Field

from datacube.core.models.enums import RGB
from datacube.core.models.exception import BadRequest

NAME_DESCRIPTION = "The name of the band requested."
VALUE_DESCRIPTION = "The expression to create the desired band. Can be " + \
    "a band of the data prefaced by its alias (ie 'S2.B05', 'S2.B12') " + \
    "or an operation on the bands (ie 'S2.B5 + S2.B8')."
DESCRIPTION_DESCRIPTION = "A description of the requested band."
MIN_DESCRIPTION = "A minimum value to clip the band values."
MAX_DESCRIPTION = "A maximum value to clip the band values."
RGB_DESCRIPTION = "Which RGB channel the band is used for the preview. " + \
    "Value can be 'RED', 'GREEN' or 'BLUE'."
CMAP_DESCRIPTION = "The matplotlib color map to use for the preview."


class Band(BaseModel):
    name: str = Field(description=NAME_DESCRIPTION)
    value: str = Field(description=VALUE_DESCRIPTION)
    description: str | None = Field(default=None,
                                    description=DESCRIPTION_DESCRIPTION)
    min: float | None = Field(default=None, description=MIN_DESCRIPTION)
    max: float | None = Field(default=None, description=MAX_DESCRIPTION)
    rgb: RGB | None = Field(default=None, description=RGB_DESCRIPTION)
    cmap: str | None = Field(default=None, description=CMAP_DESCRIPTION)

    def check_visualistion(self):
        if self.cmap is not None and self.cmap not in cm._cmap_registry:
            raise BadRequest(f"Color map '{self.cmap}' does not exist " +
                             "in matplotlib's color map registry.")
