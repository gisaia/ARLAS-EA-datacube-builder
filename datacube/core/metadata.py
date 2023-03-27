import xarray as xr
from datetime import datetime

from datacube.core.models.request.cubeBuild import ExtendedCubeBuildRequest
from datacube.core.models.metadata import HorizontalSpatialDimension, \
                                          TemporalDimension, Variable, \
                                          DatacubeMetadata
from datacube.core.models.enums import RGB


def create_datacube_metadata(request: ExtendedCubeBuildRequest,
                             datacube: xr.Dataset, x_step: float | int | None,
                             y_step: float | int | None):
    # Remove metdata created during datacube creation
    datacube.attrs = {}

    dimensions = {}
    dimensions["x"] = HorizontalSpatialDimension(
        axis="x", description="",
        extent=[float(datacube.get("x").values[0]),
                float(datacube.get("x").values[-1])],
        step=x_step, reference_system=request.target_projection
    )

    dimensions["y"] = HorizontalSpatialDimension(
        axis="y", description="",
        extent=[float(datacube.get("y").values[0]),
                float(datacube.get("y").values[-1])],
        step=y_step, reference_system=request.target_projection
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
    for raster_group in request.composition:
        composition[raster_group.timestamp] = [
            f.id for f in raster_group.rasters]

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
