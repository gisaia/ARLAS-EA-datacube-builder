from flask_restx import Model, fields

ASSET_MODEL = Model(
    "Asset",
    {
        "name": fields.String(
            required=True,
            readonly=True,
            description="The name of the asset requested. Can be a band " +
                        "of the data (ie 'B05', 'B12') or a new asset to " +
                        "integrate in the data cube (ie renaming a band," +
                        " or creating a composite one)."
        ),
        "value": fields.String(
            required=False,
            readonly=True,
            description="An optional expression to create the desired asset"
        )
    }
)


class Asset:

    def __init__(self, name, value=None):
        self.name = name
        self.value = value

    def __repr__(self):
        asset = {}
        asset["name"] = self.name
        if self.value:
            asset["value"] = self.value

        return str(asset)
