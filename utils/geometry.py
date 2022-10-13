import string
from shapely.geometry import Polygon, Point

def bbox2polygon(bbox:string):
    """
    Convert a bbox (left, bot, right, top) to a shapely Polygon
    """
    corners = bbox.split(",")

    leftbot = Point(float(corners[0]), float(corners[1]))
    lefttop = Point(float(corners[0]), float(corners[3]))
    rightbot = Point(float(corners[2]), float(corners[1]))
    righttop = Point(float(corners[2]), float(corners[3]))

    return Polygon([leftbot, rightbot, righttop, lefttop, leftbot])