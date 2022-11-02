import string

from shapely.geometry import Point, Polygon
from rasterio.warp import transform_geom


def bbox2polygon(bbox: string):
    """
    Convert a bbox (left, bot, right, top) to a shapely Polygon
    """
    corners = bbox.split(",")

    leftbot = Point(float(corners[0]), float(corners[1]))
    lefttop = Point(float(corners[0]), float(corners[3]))
    rightbot = Point(float(corners[2]), float(corners[1]))
    righttop = Point(float(corners[2]), float(corners[3]))

    return Polygon([leftbot, rightbot, righttop, lefttop, leftbot])


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
