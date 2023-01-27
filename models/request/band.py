from flask_restx import Model, fields
from utils.enums import RGB

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
        "description": fields.String(
            required=False,
            readonly=True,
            description="A description of the requested band."
        )
    }
)


class Band:

    def __init__(self, name, value=None, rgb=None, description=None):
        self.name = name
        self.value = value
        if rgb is not None:
            if rgb == RGB.RED.value:
                self.rgb = RGB.RED
            elif rgb == RGB.GREEN.value:
                self.rgb = RGB.GREEN
            elif rgb == RGB.BLUE.value:
                self.rgb = RGB.BLUE
            else:
                raise ValueError("RGB value must be 'RED', 'GREEN' or 'BLUE'")
        else:
            self.rgb = None
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
        if self.description:
            band["description"] = self.description

        return band