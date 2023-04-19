import math
import re

import numpy as np
import xarray as xr
from rasterio.warp import transform_geom
from shapely.geometry import Point, Polygon
from shapely.wkt import loads

EARTH_RADIUS = 6371000  # m


def roi2geometry(roi: str):
    """
    Convert a ROI into a shapely geometry
    """
    # If contains'(' is a WKT
    if re.match(r".*\(.*", roi):
        try:
            polygon = Polygon(loads(roi).coords)
        except Exception:
            raise ValueError("The ROI is not formatted correctly")
        if polygon.geom_type != "Polygon":
            raise TypeError("Only POLYGON geometry is supported for the ROI")
        return polygon
    # Else is a BBOX
    try:
        corners = roi.split(",")

        lb = Point(float(corners[0]), float(corners[1]))
        lt = Point(float(corners[0]), float(corners[3]))
        rb = Point(float(corners[2]), float(corners[1]))
        rt = Point(float(corners[2]), float(corners[3]))

        return Polygon([lb, rb, rt, lt, lb])
    except Exception:
        raise TypeError("Only POLYGON geometry is supported for the ROI," +
                        "in WKT or BBOX format")


def project_polygon(polygon: Polygon, src_crs: str, dst_crs: str) -> Polygon:
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


def complete_grid(lon: xr.DataArray | np.ndarray,
                  lat: xr.DataArray | np.ndarray,
                  lon_step: float, lat_step: float, bounds: tuple):
    """
    Completes the coordinates arrays to represent the full extent of 'bounds'
    (lonmin, latmin, lonmax, latmax), according to the input steps.
    """
    lon_before = np.arange(
        lon[0] - lon_step, bounds[0], -lon_step)[::-1]
    lon_after = np.arange(
        lon[-1] + lon_step, bounds[2], lon_step)

    lat_before = np.arange(
        lat[0] - lat_step, bounds[1], -lat_step)[::-1]
    lat_after = np.arange(
        lat[-1] + lon_step, bounds[3], lat_step)

    grid_lon = np.concatenate(
        (lon_before, lon, lon_after))
    grid_lat = np.concatenate(
        (lat_before, lat, lat_after))

    # If missing an element, add the furthest from the bounds
    if len(grid_lon) < math.ceil((bounds[2] - bounds[0]) / lon_step):
        if abs(grid_lon[-1] - bounds[2]) < abs(grid_lon[0] - bounds[0]):
            grid_lon = np.concatenate(
                ([grid_lon[0] - lon_step], grid_lon))
        else:
            grid_lon = np.concatenate(
                (grid_lon, [grid_lon[-1] + lon_step]))
    # If one extra element, remove the furthest from the bounds
    elif len(grid_lon) > math.ceil((bounds[2] - bounds[0]) / lon_step):
        if abs(grid_lon[-1] - bounds[2]) < abs(grid_lon[0] - bounds[0]):
            grid_lon = grid_lon[1:]
        else:
            grid_lon = grid_lon[:-1]

    # If missing an element, add the furthest from the bounds
    if len(grid_lat) < math.ceil((bounds[3] - bounds[1]) / lat_step):
        if abs(grid_lat[-1] - bounds[3]) < abs(grid_lat[0] - bounds[1]):
            grid_lat = np.concatenate(
                ([grid_lat[0] - lat_step], grid_lat))
        else:
            grid_lat = np.concatenate(
                (grid_lat, [grid_lat[-1] + lat_step]))
    # If one extra element, remove the furthest from the bounds
    elif len(grid_lat) > math.ceil((bounds[3] - bounds[1]) / lat_step):
        if abs(grid_lat[-1] - bounds[2]) < abs(grid_lat[0] - bounds[0]):
            grid_lat = grid_lat[1:]
        else:
            grid_lat = grid_lat[:-1]

    return grid_lon, grid_lat
