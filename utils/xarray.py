import xarray as xr
import enum
from typing import List
import numpy as np


class IntersectionType(enum.Enum):
    LEFT = "left"
    BOTTOM = "bottom"
    RIGHT = "right"
    TOP = "top"
    SAME = "same"


DTYPE_BYTES = {
    'byte': 1,
    'uint16': 2,
    'int16': 2,
    'uint32': 4,
    'int32': 4,
    'float32': 4,
    'float64': 8,
}


def getChunkSize(dtype: str, chunkMbs: float = 1):
    # TODO: chunk size is not the correct one in the end
    return int((chunkMbs * 1e6/DTYPE_BYTES[dtype])**0.5)


def getChunkShape(dtype: str, chunkMbs: float = 1):
    return (getChunkSize(dtype, chunkMbs),
            getChunkSize(dtype, chunkMbs), 1)


def getBounds(ds: xr.Dataset):
    return (float(ds.get("x").min()),
            float(ds.get("y").min()),
            float(ds.get("x").max()),
            float(ds.get("y").max()))


def intersect(firstDataset: xr.Dataset,
              secondDataset: xr.Dataset) -> List[IntersectionType]:
    firstBounds = getBounds(firstDataset)
    secondBounds = getBounds(secondDataset)

    if firstBounds == secondBounds:
        return [IntersectionType.SAME]

    intersections = []
    if firstBounds[0] < secondBounds[2] < firstBounds[2]:
        intersections.append(IntersectionType.LEFT)
    if firstBounds[1] < secondBounds[3] < firstBounds[3]:
        intersections.append(IntersectionType.BOTTOM)
    if firstBounds[0] < secondBounds[0] < firstBounds[2]:
        intersections.append(IntersectionType.RIGHT)
    if firstBounds[1] < secondBounds[1] < firstBounds[3]:
        intersections.append(IntersectionType.TOP)

    return np.array(intersections)


def mergeDatasets(firstDataset: xr.Dataset,
                  secondDataset: xr.Dataset) -> xr.Dataset:
    intersectTypes = intersect(firstDataset, secondDataset)

    # If no intersections, auto-magically combine
    if len(intersectTypes) == 0:
        return xr.combine_by_coords(
            (firstDataset, secondDataset), combine_attrs="override")

    # If they represent the same extent of data, merge based on criterion
    if IntersectionType.SAME in intersectTypes:
        if firstDataset.attrs["productTimestamp"] \
           >= secondDataset.attrs["productTimestamp"]:
            return firstDataset.combine_first(secondDataset)
        else:
            return secondDataset.combine_first(firstDataset)

    firstBounds = getBounds(firstDataset)
    secondBounds = getBounds(secondDataset)

    # Resolve overlapping counter-clockwise
    if IntersectionType.LEFT in intersectTypes:
        left = secondDataset.where(
            secondDataset.x < firstBounds[0], drop=True)
        firstDSIntersection = firstDataset.where(
            firstDataset.x <= secondBounds[2], drop=True)
        secondDSIntersection = secondDataset.where(
            secondDataset.x >= firstBounds[0], drop=True)
        intersection = mergeDatasets(firstDSIntersection, secondDSIntersection)
        right = firstDataset.where(
            firstDataset.x > secondBounds[2], drop=True)
        return xr.concat([left, intersection, right], dim="x")

    if IntersectionType.BOTTOM in intersectTypes:
        bottom = secondDataset.where(
            secondDataset.y < firstBounds[1], drop=True)
        firstDSIntersection = firstDataset.where(
            firstDataset.y <= secondBounds[3], drop=True)
        secondDSIntersection = secondDataset.where(
            secondDataset.y >= firstBounds[1], drop=True)
        intersection = mergeDatasets(firstDSIntersection, secondDSIntersection)
        top = firstDataset.where(
            firstDataset.y > secondBounds[3], drop=True)
        return xr.concat([bottom, intersection, top], dim="y")

    if IntersectionType.RIGHT in intersectTypes:
        left = firstDataset.where(
            firstDataset.x < secondBounds[0], drop=True)
        firstDSIntersection = firstDataset.where(
            firstDataset.x >= secondBounds[0], drop=True)
        secondDSIntersection = secondDataset.where(
            secondDataset.x <= firstBounds[2], drop=True)
        intersection = mergeDatasets(firstDSIntersection, secondDSIntersection)
        right = secondDataset.where(
            secondDataset.x > firstBounds[2], drop=True)
        return xr.concat([left, intersection, right], dim="x")

    if IntersectionType.TOP in intersectTypes:
        bottom = firstDataset.where(
            firstDataset.y < secondBounds[1], drop=True)
        firstDSIntersection = firstDataset.where(
            firstDataset.y >= secondBounds[1], drop=True)
        secondDSIntersection = secondDataset.where(
            secondDataset.y <= firstBounds[3], drop=True)
        intersection = mergeDatasets(firstDSIntersection, secondDSIntersection)
        top = secondDataset.where(
            secondDataset.y > firstBounds[3], drop=True)
        return xr.concat([bottom, intersection, top], dim="y")
