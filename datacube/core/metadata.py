import math
import re
from datetime import datetime

import xarray as xr
from shapely.geometry import Polygon

from datacube.core.cache.cache_manager import CacheManager
from datacube.core.geo.utils import bbox2polygon, project_polygon
from datacube.core.models.enums import RGB
from datacube.core.models.metadata import (DatacubeMetadata, DimensionType,
                                           HorizontalSpatialDimension,
                                           QualityIndicators,
                                           QualityIndicatorsCube,
                                           TemporalDimension, Variable)
from datacube.core.models.request.cubeBuild import ExtendedCubeBuildRequest
from datacube.core.models.request.rasterGroup import RasterGroup
from datacube.core.rasters.drivers.abstract import CachedAbstractRasterArchive


def create_datacube_metadata(request: ExtendedCubeBuildRequest,
                             datacube: xr.Dataset, x_step: float | int | None,
                             y_step: float | int | None) -> DatacubeMetadata:
    # Remove metdata created during datacube creation
    datacube.attrs = {}

    dimensions = {}
    dimensions["x"] = HorizontalSpatialDimension(
        type=DimensionType.SPATIAL, axis="x", description="",
        extent=[float(datacube.get("x").values[0]),
                float(datacube.get("x").values[-1])],
        step=x_step, reference_system=request.target_projection
    )

    dimensions["y"] = HorizontalSpatialDimension(
        type=DimensionType.SPATIAL, axis="y", description="",
        extent=[float(datacube.get("y").values[0]),
                float(datacube.get("y").values[-1])],
        step=y_step, reference_system=request.target_projection
    )

    t_step = None
    if len(datacube.get("t")) != 1:
        t_step = str(datacube.get("t").diff("t").sum().values
                     / (len(datacube.get("t")) - 1))
    dimensions["t"] = TemporalDimension(
        type=DimensionType.TEMPORAL, axis="t", description="",
        extent=[datetime.fromtimestamp(
                    datacube.get("t").values[0]).isoformat(),
                datetime.fromtimestamp(
                    datacube.get("t").values[-1]).isoformat()],
        step=t_step
    )

    variables = {}
    for band in request.bands:
        variables[band.name] = Variable(
            dimensions=["x", "y", "t"],
            type="data", description=band.description,
            extent=[datacube.get(band.name).min().values.tolist(),
                    datacube.get(band.name).max().values.tolist()],
            unit=band.unit, expression=band.value
        )

    # If all colors have been assigned, use them for the preview
    if len(request.rgb) == 3:
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

    number_of_chunks = 1
    for chunks in datacube.chunks.values():
        number_of_chunks *= len(chunks)

    data_weight = list(datacube.variables.values())[0].data.dtype.itemsize
    chunk_weight = datacube.chunks['x'][0] * datacube.chunks['y'][0] \
        * datacube.chunks['t'][0] * data_weight

    cache_client = CacheManager()

    composition_start = math.inf
    composition_end = -math.inf

    composition_by_type: list[dict[str,
                                   list[CachedAbstractRasterArchive]]] = []
    for group in request.composition:
        group_composition: dict[str, list[CachedAbstractRasterArchive]] = {}
        for r in group.rasters:
            raster = cache_client.get(r.path)
            if raster:
                # Split the rasters by timestamp and product type
                if raster.type.to_key() in group_composition:
                    group_composition[raster.type.to_key()].append(raster)
                else:
                    group_composition[raster.type.to_key()] = [raster]

                # Find the first and last timestamp
                if raster.timestamp < composition_start:
                    composition_start = raster.timestamp
                if raster.timestamp > composition_end:
                    composition_end = raster.timestamp
            else:
                raise Exception(
                    f'Raster "{r.path}" was not found in the cache manager')
        composition_by_type.append(group_composition)

    timespan = composition_start - composition_end
    indicators_per_group_per_type: list[dict[str, QualityIndicators]] = []

    for group in composition_by_type:
        group_indicators_per_type = {}

        # Split rasters of the group by type
        for type, rasters in group.items():
            group_indicators_per_type[type] = QualityIndicators(
                time_compacity=compute_time_compacity(
                    rasters, timespan),
                spatial_coverage=compute_spatial_coverage(
                    rasters, request.roi_polygon, request.target_projection),
                group_lightness=compute_group_lightness(
                    rasters, request.roi_polygon, request.target_projection))
        indicators_per_group_per_type.append(group_indicators_per_type)

    # For the group, the indicator is the product of those of each type
    group_indicators: dict[str, dict[str, float]] = {}
    for idx, group in enumerate(indicators_per_group_per_type):
        group_indicators[str(request.composition[idx].timestamp)] = \
                QualityIndicators(
                    time_compacity=math.prod(
                        map(lambda t: t.time_compacity, group.values())),
                    spatial_coverage=math.prod(
                        map(lambda t: t.spatial_coverage, group.values())),
                    group_lightness=math.prod(
                        map(lambda t: t.group_lightness, group.values()))
                ).dict()

    # The group indicators are stored with the time coordinates
    datacube.get('t').attrs.update(group_indicators)

    # For the type, the indicator is the product of those of each group
    # of the desired type
    type_indicators: dict[str, QualityIndicators] = {}
    for type in request.aliases:
        type_key = type.to_key()
        type_indicators[type_key] = QualityIndicators(
            time_compacity=math.prod(
                map(lambda g: g[type_key].time_compacity if type_key in g
                    else 1, indicators_per_group_per_type)),
            spatial_coverage=math.prod(
                map(lambda g: g[type_key].spatial_coverage if type_key in g
                    else 1, indicators_per_group_per_type)),
            group_lightness=math.prod(
                map(lambda g: g[type_key].group_lightness if type_key in g
                    else 1, indicators_per_group_per_type)))

    band_indicators: dict[str, QualityIndicators] = {}
    for band in request.bands:
        # Find which product types constitute the band
        aliases_in_band = re.findall(r'([a-zA-Z0-9]*)\.[a-zA-Z0-9]*',
                                     band.value)
        types_in_band = []
        for alias in aliases_in_band:
            for type in request.aliases:
                if type.alias == alias:
                    types_in_band.append(type.to_key())
                    break

        # Compute the indicator as a product of the those of the products
        # used to compute the band
        band_indicators[band.name] = QualityIndicators(
            time_compacity=math.prod(
                map(lambda t: type_indicators[t].time_compacity,
                    types_in_band)),
            spatial_coverage=math.prod(
                map(lambda t: type_indicators[t].spatial_coverage,
                    types_in_band)),
            group_lightness=math.prod(
                map(lambda t: type_indicators[t].group_lightness,
                    types_in_band)))
        # Add indicator to the datacube
        datacube.get(band.name).attrs.update(band_indicators[band.name].dict())

    # For the cube, the indicator is the product of those of each group
    cube_indicators = QualityIndicatorsCube(
        time_compacity=math.prod(
            map(lambda g: g['time_compacity'], group_indicators.values())),
        spatial_coverage=math.prod(
            map(lambda g: g['spatial_coverage'], group_indicators.values())),
        group_lightness=math.prod(
            map(lambda g: g['group_lightness'], group_indicators.values())),
        time_regularity=compute_time_regularity(request.composition))

    # Fill ratio is the average of how much each band is filled
    fill_ratio = 0
    cube_size = len(datacube.x) * len(datacube.y) * len(datacube.t)
    for band in datacube.data_vars.values():
        fill_ratio += 1 - band.isnull().sum().compute().values / cube_size
    fill_ratio = fill_ratio / len(datacube.data_vars)

    return DatacubeMetadata(**{
        "cube:dimensions": dimensions,
        "cube:variables": variables,
        "dc3:composition": request.composition,
        "dc3:preview": preview,
        "dc3:number_of_chunks": number_of_chunks,
        "dc3:chunk_weight": chunk_weight,
        "dc3:quality_indicators": cube_indicators,
        "dc3:fill_ratio": fill_ratio})


def compute_time_compacity(rasters: list[CachedAbstractRasterArchive],
                           timespan: int) -> float:
    """
    Computes how compact time-wise the list of rasters is in regards to
    the global timespan of the datacube.

    The time compacity corresponds to 1 - (t_max - t_min) / timespan
    """
    if timespan == 0:
        return 1
    raster_times = list(map(lambda r: r.timestamp, rasters))

    return 1 - (max(raster_times) - min(raster_times)) / timespan


def compute_spatial_coverage(rasters: list[CachedAbstractRasterArchive],
                             roi: Polygon, dst_crs: str) -> float:
    """
    Computes how well the list of rasters cover the desired ROI.

    The spatial coverage corresponds to area(U(polygon)) / area(ROI).
    """
    # Compute the polygon representing the raster in the desired projection
    raster_polygons = list(map(lambda r: project_polygon(bbox2polygon(
        r.left, r.bottom, r.right, r.top), r.crs, dst_crs), rasters))

    polygon_union = raster_polygons[0]
    for polygon in raster_polygons:
        polygon_union = polygon_union.union(polygon)
    polygon_union = polygon_union.intersection(roi)

    return polygon_union.area / roi.area


def compute_group_lightness(rasters: list[CachedAbstractRasterArchive],
                            roi: Polygon, dst_crs: str) -> float:
    """
    Computes how little redundant geographic information is carried
    in the input list of rasters.

    The group lightness corresponds to area(U(polygon)) / S(area(polygon)).
    """
    # Compute the polygon representing the raster in the desired projection
    raster_polygons = list(map(lambda r: project_polygon(bbox2polygon(
        r.left, r.bottom, r.right, r.top), r.crs, dst_crs), rasters))

    polygon_union = raster_polygons[0]
    for polygon in raster_polygons:
        polygon_union = polygon_union.union(polygon)
    polygon_union = polygon_union.intersection(roi)

    sum_areas = sum(map(lambda p: p.area, raster_polygons))

    return polygon_union.area / sum_areas


def compute_time_regularity(composition: list[RasterGroup]) -> float:
    """
    Computes an indicator of how regularly spaced
    the time slices of a datacube is.

    The time regularity corresponds to 1 - std(timeDeltas)/avg(timeDeltas).
    """
    if len(composition) == 1:
        return 1

    delta_times = []

    for i in range(len(composition) - 1):
        delta_times.append(
            composition[i + 1].timestamp - composition[i].timestamp)
    avg_delta_time = sum(delta_times) / len(delta_times)

    return 1 - math.sqrt(sum(
        map(lambda t: math.pow(t - avg_delta_time, 2), delta_times)
            ) / len(delta_times)) / avg_delta_time
