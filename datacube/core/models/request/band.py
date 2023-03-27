from typing import Annotated
from fastapi import Query
from pydantic import BaseModel
from matplotlib import cm

from datacube.core.models.enums import RGB
from datacube.core.models.errors import BadRequest

NAME_DESCRIPTION = "Name of the band requested"
VALUE_DESCRIPTION = "Expression to create the desired band. Can be " + \
    "a band of the data prefaced by its alias (ie 'S2.B05', 'S2.B12') " + \
    "or an operation on the bands (ie 'S2.B5 + S2.B8')."
DESCRIPTION_DESCRIPTION = "A description of the requested band."
MIN_DESCRIPTION = "A minimum value to clip the band."
MAX_DESCRIPTION = "A maximum value to clip the band."
RGB_DESCRIPTION = "Which RGB channel the band is used for the preview. " + \
    "Value can be 'RED', 'GREEN' or 'BLUE'."
CMAP_DESCRIPTION = "The matplotlib color map to use for the preview."


class Band(BaseModel):
    name: Annotated[
        str, Query(description=NAME_DESCRIPTION)]
    value: Annotated[
        str, Query(description=VALUE_DESCRIPTION)]
    description: Annotated[
        str | None, Query(description=DESCRIPTION_DESCRIPTION)] = None
    min: Annotated[
        float | None, Query(description=MIN_DESCRIPTION)] = None
    max: Annotated[
        float | None, Query(description=MAX_DESCRIPTION)] = None
    rgb: Annotated[
        RGB | None, Query(description=RGB_DESCRIPTION)] = None
    cmap: Annotated[
        str | None, Query(description=CMAP_DESCRIPTION)] = None

    def check_visualistion(self):
        if self.cmap is not None and self.cmap not in cm._cmap_registry:
            raise BadRequest(f"Color map '{self.cmap}' does not exist " +
                             "in matplotlib's color map registry.")
