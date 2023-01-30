import xarray as xr
from datetime import datetime

from models.request.datacube_build import DatacubeBuildRequest
from models.metadata import HorizontalSpatialDimension, \
                            TemporalDimension, Variable, \
                            DatacubeMetadata


def create_datacube_metadata(request: DatacubeBuildRequest,
                             datacube: xr.Dataset, xStep, yStep):
    # From datacube get variables and dimensions
    # Steps are not perfectly regular
    # (due to the earth deformation on center granule)
    dimensions = {}
    dimensions["x"] = HorizontalSpatialDimension(
        axis="x", description="",
        extent=[datacube.get("x").values[0],
                datacube.get("x").values[-1]],
        step=xStep, reference_system=request.targetProjection
    )

    dimensions["y"] = HorizontalSpatialDimension(
        axis="y", description="",
        extent=[datacube.get("y").values[0],
                datacube.get("y").values[-1]],
        step=yStep, reference_system=request.targetProjection
    )

    dimensions["t"] = TemporalDimension(
        axis="t", description="",
        extent=[datetime.fromtimestamp(
                    datacube.get("t").values[0]).isoformat(),
                datetime.fromtimestamp(
                    datacube.get("t").values[-1]).isoformat()],
        step=None
    )

    variables = {}
    for band in request.bands:
        variables[band.name] = Variable(
            dimensions=["x", "y", "t"],
            type="data", description=band.description,
            extent=[datacube.get(band.name).min().values.tolist(),
                    datacube.get(band.name).max().values.tolist()],
            unit="", expression=band.value
        )

    composition = {}
    for rasterGroup in request.composition:
        composition[rasterGroup.timestamp] = [
            f.id for f in rasterGroup.rasters]

    metadata = DatacubeMetadata(dimensions, variables, composition)
    return datacube.assign_attrs(metadata.as_dict())
