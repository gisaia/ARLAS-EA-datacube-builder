from flask_restx import Model, fields

DATACUBE_BUILD_RESPONSE = Model(
    "DatacubeBuildResponse",
    {
        "datacubeURL": fields.String(
            description="The URL at which the datacube is created")
    }
)
