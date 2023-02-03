import math
import re

from shapely.geometry import Point, Polygon
from shapely.wkt import loads
from rasterio.warp import transform_geom
import numpy as np
import xarray as xr

EARTH_RADIUS = 6371000  # m


def roi2geometry(roi: str):
    """
    Convert a ROI into a shapely geometry
    """
    # If contains'(' is a WKT
    if re.match(r".*\(.*", roi):
        try:
            polygon = loads(roi)
        except Exception:
            raise ValueError("The ROI is not formatted correctly")
        if polygon.geom_type != "Polygon":
            raise TypeError("Only POLYGON geometry is supported for the ROI")
        return polygon
    # Else is a BBOX
    try:
        corners = roi.split(",")

        leftbot = Point(float(corners[0]), float(corners[1]))
        lefttop = Point(float(corners[0]), float(corners[3]))
        rightbot = Point(float(corners[2]), float(corners[1]))
        righttop = Point(float(corners[2]), float(corners[3]))

        return Polygon([leftbot, rightbot, righttop, lefttop, leftbot])
    except Exception:
        raise TypeError("Only POLYGON geometry is supported for the ROI," +
                        "in WKT or BBOX format")


def projectPolygon(polygon: Polygon, src_crs: str, dst_crs: str) -> Polygon:
    """
    Project a polygon in the desired projection
    """
    x, y = polygon.exterior.coords.xy

    return Polygon(transform_geom(
        src_crs, dst_crs,
        {
            'type': polygon.geom_type,
            'coordinates': [list(zip(x, y))]
        })["coordinates"][0])


def completeGrid(longitudes: xr.DataArray | np.ndarray,
                 latitudes: xr.DataArray | np.ndarray,
                 longitudeStep: float, latitudeStep: float, bounds: tuple):
    """
    Completes the coordinates arrays to represent the full extent of 'bounds'
    (lonmin, latmin, lonmax, latmax), according to the input steps.
    """
    longitudesBefore = np.arange(
        longitudes[0] - longitudeStep, bounds[0], -longitudeStep)[::-1]
    longitudesAfter = np.arange(
        longitudes[-1] + longitudeStep, bounds[2], longitudeStep)

    latitudesBefore = np.arange(
        latitudes[0] - latitudeStep, bounds[1], -latitudeStep)[::-1]
    latitudesAfter = np.arange(
        latitudes[-1] + longitudeStep, bounds[3], latitudeStep)

    extendedLon = np.concatenate(
        (longitudesBefore, longitudes, longitudesAfter))
    extendedLat = np.concatenate(
        (latitudesBefore, latitudes, latitudesAfter))

    # If missing an element, add the furthest from the bounds
    if len(extendedLon) < math.ceil((bounds[2] - bounds[0]) / longitudeStep):
        if abs(extendedLon[-1] - bounds[2]) < abs(extendedLon[0] - bounds[0]):
            extendedLon = np.concatenate(
                ([extendedLon[0] - longitudeStep], extendedLon))
        else:
            extendedLon = np.concatenate(
                (extendedLon, [extendedLon[-1] + longitudeStep]))
    # If one extra element, remove the furthest from the bounds
    elif len(extendedLon) > math.ceil((bounds[2] - bounds[0]) / longitudeStep):
        if abs(extendedLon[-1] - bounds[2]) < abs(extendedLon[0] - bounds[0]):
            extendedLon = extendedLon[1:]
        else:
            extendedLon = extendedLon[:-1]

    # If missing an element, add the furthest from the bounds
    if len(extendedLat) < math.ceil((bounds[3] - bounds[1]) / latitudeStep):
        if abs(extendedLat[-1] - bounds[3]) < abs(extendedLat[0] - bounds[1]):
            extendedLat = np.concatenate(
                ([extendedLat[0] - latitudeStep], extendedLat))
        else:
            extendedLat = np.concatenate(
                (extendedLat, [extendedLat[-1] + latitudeStep]))
    # If one extra element, remove the furthest from the bounds
    elif len(extendedLat) > math.ceil((bounds[3] - bounds[1]) / latitudeStep):
        if abs(extendedLat[-1] - bounds[2]) < abs(extendedLat[0] - bounds[0]):
            extendedLat = extendedLat[1:]
        else:
            extendedLat = extendedLat[:-1]

    return extendedLon, extendedLat
