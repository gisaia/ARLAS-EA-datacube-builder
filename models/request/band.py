from flask_restx import Model, fields
from utils.enums import RGB
from models.errors import BadRequest

from matplotlib import cm


BAND_MODEL = Model(
    "Band",
    {
        "name": fields.String(
            required=True,
            readonly=True,
            description="The name of the band requested. Can be a band " +
                        "of the data (ie 'B05', 'B12') or a new band to " +
                        "integrate in the data cube (ie renaming a band," +
                        " or creating a composite one)."
        ),
        "value": fields.String(
            required=False,
            readonly=True,
            description="An optional expression to create the desired band."
        ),
        "rgb": fields.String(
            required=False,
            readonly=True,
            description="Specifies if the band is used for " +
                        "the RGB preview of the datacube.",
            enum=['RED', 'GREEN', 'BLUE']
        ),
        "cmap": fields.String(
            required=False,
            readonly=True,
            description="The matplotlib color map to use for " +
                        "the datacube's preview."
        ),
        "description": fields.String(
            required=False,
            readonly=True,
            description="A description of the requested band."
        )
    }
)


class Band:

    def __init__(self, name, value=None, rgb=None,
                 cmap=None, description=None):
        self.name: str = name
        self.value = value
        if rgb is not None:
            if rgb == RGB.RED.value:
                self.rgb = RGB.RED
            elif rgb == RGB.GREEN.value:
                self.rgb = RGB.GREEN
            elif rgb == RGB.BLUE.value:
                self.rgb = RGB.BLUE
            else:
                raise BadRequest("RGB value must be 'RED', 'GREEN' or 'BLUE'")
        else:
            self.rgb = None

        if cmap is not None:
            if cmap not in cm._cmap_registry:
                raise BadRequest(f"Color map '{cmap}' does not exist " +
                                 "in matplotlib's color map registry.")
            self.cmap = cmap
        self.description = description

    def __repr__(self):
        return str(self.as_dict())

    def as_dict(self):
        band = {}
        band["name"] = self.name
        if self.value:
            band["value"] = self.value
        if self.rgb:
            band["rgb"] = self.rgb
        if self.cmap:
            band["cmap"] = self.cmap
        if self.description:
            band["description"] = self.description

        return band
