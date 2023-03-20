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
            description="Name of the band requested"
        ),
        "value": fields.String(
            required=True,
            readonly=True,
            description="Expression to create the desired band. " +
                        "Can be a band of the data prefaced by its alias " +
                        "(ie 'S2.B05', 'S2.B12') or an operation on the " +
                        "bands (ie 'S2.B5 + S2.B8')."
        ),
        "min": fields.Float(
            required=False,
            readonly=False,
            description="A minimum value to clip the band."
        ),
        "max": fields.Float(
            required=False,
            readonly=False,
            description="A maximum value to clip the band."
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

    def __init__(self, name, value=None, min=None, max=None,
                 rgb=None, cmap=None, description=None):
        self.name: str = name
        self.value = value
        self.min = min
        self.max = max
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

        self.cmap = cmap
        if cmap is not None and cmap not in cm._cmap_registry:
            raise BadRequest(f"Color map '{cmap}' does not exist " +
                             "in matplotlib's color map registry.")
        self.description = description

    def __repr__(self):
        return str(self.as_dict())

    def as_dict(self):
        band = {}
        band["name"] = self.name
        if self.value:
            band["value"] = self.value
        if self.min:
            band["min"] = self.min
        if self.max:
            band["max"] = self.max
        if self.rgb:
            band["rgb"] = self.rgb
        if self.cmap:
            band["cmap"] = self.cmap
        if self.description:
            band["description"] = self.description

        return band
