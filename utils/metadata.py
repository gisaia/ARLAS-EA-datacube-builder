import xarray as xr
from datetime import datetime

from models.request.cubeBuild import CubeBuildRequest
from models.metadata import HorizontalSpatialDimension, \
                            TemporalDimension, Variable, \
                            DatacubeMetadata
from utils.enums import RGB


def create_datacube_metadata(request: CubeBuildRequest,
                             datacube: xr.Dataset, xStep, yStep):
    # Remove metdata created during datacube creation
    datacube.attrs = {}

    dimensions = {}
    dimensions["x"] = HorizontalSpatialDimension(
        axis="x", description="",
        extent=[float(datacube.get("x").values[0]),
                float(datacube.get("x").values[-1])],
        step=xStep, reference_system=request.targetProjection
    )

    dimensions["y"] = HorizontalSpatialDimension(
        axis="y", description="",
        extent=[float(datacube.get("y").values[0]),
                float(datacube.get("y").values[-1])],
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

    # If all colors have been assigned, use them for the preview
    if request.rgb != {}:
        preview = {"RED": request.rgb[RGB.RED],
                   "GREEN": request.rgb[RGB.GREEN],
                   "BLUE": request.rgb[RGB.BLUE]}
    # Else use the first band of the datacube with a cmap or default cmap
    else:
        preview = {"rainbow": list(datacube.data_vars.keys())[0]}
        for band in request.bands:
            if band.cmap is not None:
                preview = {band.cmap: band.name}
                break

    metadata = DatacubeMetadata(dimensions, variables, composition, preview)
    return datacube.assign_attrs(metadata.as_dict())
