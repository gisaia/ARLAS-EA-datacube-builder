import xarray as xr
import enum
from typing import List, Dict
import numpy as np

from .enums import ChunkingStrategy as CStrat


class IntersectionType(enum.Enum):
    LEFT = "left"
    BOTTOM = "bottom"
    RIGHT = "right"
    TOP = "top"
    SAME = "same"


POTATO_CHUNK = {"x": 256, "y": 256, "t": 32}
CARROT_CHUNK = {"x": 32, "y": 32, "t": 1024}
SPINACH_CHUNK = {"x": 1024, "y": 1024, "t": 1}


def getChunkShape(dims: Dict[str, int],
                  chunkingStrategy: CStrat = CStrat.POTATO) -> Dict[str, int]:
    """
    Generates chunks of pre-determined size based on a desired strategy.
    For 'uint32' and 'int32' data types, they result in ~8Mb chunks.
    """

    def resizeTimeDepth(chunkShape: Dict[str, int], dims: Dict[str, int]):
        while dims["t"] <= chunkShape["t"] / 4:
            chunkShape["x"] *= 2
            chunkShape["y"] *= 2
            chunkShape["t"] = int(chunkShape["t"]/4)
        return chunkShape

    if chunkingStrategy == CStrat.POTATO:
        chunkShape = resizeTimeDepth(POTATO_CHUNK, dims)
    elif chunkingStrategy == CStrat.CARROT:
        chunkShape = resizeTimeDepth(CARROT_CHUNK, dims)
    elif chunkingStrategy == CStrat.SPINACH:
        chunkShape = SPINACH_CHUNK
    else:
        raise ValueError(f"Chunking strategy '{chunkingStrategy}' not defined")

    chunkShape["x"] = min(chunkShape["x"], dims["x"])
    chunkShape["y"] = min(chunkShape["y"], dims["y"])
    chunkShape["t"] = min(chunkShape["t"], dims["t"])
    return chunkShape


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
    if firstDataset is None:
        return secondDataset
    if secondDataset is None:
        return firstDataset

    intersectTypes = intersect(firstDataset, secondDataset)

    # If no intersections, auto-magically combine
    if len(intersectTypes) == 0:
        return xr.combine_by_coords(
            (firstDataset, secondDataset), combine_attrs="override")

    # If they represent the same extent of data, merge based on criterion
    if IntersectionType.SAME in intersectTypes:
        if firstDataset.get("t").values[0] \
           >= secondDataset.get("t").values[0]:
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
