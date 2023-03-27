import xarray as xr
import enum
from typing import List, Dict
import numpy as np

from datacube.core.models.enums import ChunkingStrategy as CStrat


class IntersectionType(enum.Enum):
    LEFT = "left"
    BOTTOM = "bottom"
    RIGHT = "right"
    TOP = "top"
    SAME = "same"


POTATO_CHUNK = {"x": 256, "y": 256, "t": 32}
CARROT_CHUNK = {"x": 32, "y": 32, "t": 1024}
SPINACH_CHUNK = {"x": 1024, "y": 1024, "t": 1}


def get_chunk_shape(dims: Dict[str, int],
                    chunking_strat: CStrat = CStrat.POTATO) -> Dict[str, int]:
    """
    Generates chunks of pre-determined size based on a desired strategy.
    For 'uint32' and 'int32' data types, they result in ~8Mb chunks.
    """

    def resize_time_depth(chunk_shape: Dict[str, int], dims: Dict[str, int]):
        while dims["t"] <= chunk_shape["t"] / 4:
            chunk_shape["x"] *= 2
            chunk_shape["y"] *= 2
            chunk_shape["t"] = int(chunk_shape["t"]/4)
        return chunk_shape

    if chunking_strat == CStrat.POTATO:
        chunk_shape = resize_time_depth(POTATO_CHUNK, dims)
    elif chunking_strat == CStrat.CARROT:
        chunk_shape = resize_time_depth(CARROT_CHUNK, dims)
    elif chunking_strat == CStrat.SPINACH:
        chunk_shape = SPINACH_CHUNK
    else:
        raise ValueError(f"Chunking strategy '{chunking_strat}' not defined")

    chunk_shape["x"] = min(chunk_shape["x"], dims["x"])
    chunk_shape["y"] = min(chunk_shape["y"], dims["y"])
    chunk_shape["t"] = min(chunk_shape["t"], dims["t"])
    return chunk_shape


def get_bounds(ds: xr.Dataset):
    return (float(ds.get("x").min()),
            float(ds.get("y").min()),
            float(ds.get("x").max()),
            float(ds.get("y").max()))


def intersect(first_dataset: xr.Dataset,
              second_dataset: xr.Dataset) -> List[IntersectionType]:
    first_bounds = get_bounds(first_dataset)
    second_bounds = get_bounds(second_dataset)

    if first_bounds == second_bounds:
        return [IntersectionType.SAME]

    intersections = []
    if first_bounds[0] < second_bounds[2] < first_bounds[2]:
        intersections.append(IntersectionType.LEFT)
    if first_bounds[1] < second_bounds[3] < first_bounds[3]:
        intersections.append(IntersectionType.BOTTOM)
    if first_bounds[0] < second_bounds[0] < first_bounds[2]:
        intersections.append(IntersectionType.RIGHT)
    if first_bounds[1] < second_bounds[1] < first_bounds[3]:
        intersections.append(IntersectionType.TOP)

    return np.array(intersections)


def merge_datasets(first_dataset: xr.Dataset,
                   second_dataset: xr.Dataset) -> xr.Dataset:
    """
    Merge two datasets based on their geographical bounds as well as
    their bands. Performs a mosaicking for the bands in common, while just
    appending the other bands to the resulting dataset.
    """

    if first_dataset is None:
        return second_dataset
    if second_dataset is None:
        return first_dataset

    # It is only possible to concatenate datasets that contain the same bands
    common_bands = []
    for band in first_dataset.data_vars.keys():
        if band in second_dataset.data_vars.keys():
            common_bands.append(band)

    # If they intersect in any way but don't hold the same data,
    # then no mosaickin is needed
    if len(common_bands) == 0:
        return xr.merge(
            (first_dataset, second_dataset), combine_attrs="override")

    rest_first_ds = first_dataset[
        list(set(first_dataset.data_vars.keys()).difference(common_bands))]
    common_first_ds = first_dataset[common_bands]

    rest_second_ds = second_dataset[
        list(set(second_dataset.data_vars.keys()).difference(common_bands))]
    commonSecondDS = second_dataset[common_bands]

    return xr.merge(
        (_mosaicking(common_first_ds, commonSecondDS),
         rest_first_ds, rest_second_ds), combine_attrs="override")


def _mosaicking(first_dataset: xr.Dataset,
                second_dataset: xr.Dataset) -> xr.Dataset:

    intersection_types = intersect(first_dataset, second_dataset)

    # If no intersections, auto-magically combine
    if len(intersection_types) == 0:
        return xr.combine_by_coords(
            (first_dataset, second_dataset), combine_attrs="override")

    # If they represent the same extent of data, merge based on criterion
    if IntersectionType.SAME in intersection_types:
        if first_dataset.attrs["product_timestamp"] \
                >= second_dataset.attrs["product_timestamp"]:
            ds = first_dataset.combine_first(second_dataset) \
                    .assign_attrs({"product_timestamp":
                                   first_dataset.attrs["product_timestamp"]})
            return ds
        else:
            ds = second_dataset.combine_first(first_dataset) \
                    .assign_attrs({"product_timestamp":
                                   second_dataset.attrs["product_timestamp"]})
            return ds

    first_bounds = get_bounds(first_dataset)
    second_bounds = get_bounds(second_dataset)

    # Resolve overlapping counter-clockwise
    if IntersectionType.LEFT in intersection_types:
        left = second_dataset.where(
            second_dataset.x < first_bounds[0], drop=True)
        first_ds_intersection = first_dataset.where(
            first_dataset.x <= second_bounds[2], drop=True)
        second_ds_intersection = second_dataset.where(
            second_dataset.x >= first_bounds[0], drop=True)
        intersection = _mosaicking(first_ds_intersection,
                                   second_ds_intersection)
        right = first_dataset.where(
            first_dataset.x > second_bounds[2], drop=True)
        if len(left.x) == 0:
            return xr.concat([intersection, right], dim="x")
        return xr.concat([left, intersection, right], dim="x")

    if IntersectionType.BOTTOM in intersection_types:
        bottom = second_dataset.where(
            second_dataset.y < first_bounds[1], drop=True)
        first_ds_intersection = first_dataset.where(
            first_dataset.y <= second_bounds[3], drop=True)
        second_ds_intersection = second_dataset.where(
            second_dataset.y >= first_bounds[1], drop=True)
        intersection = _mosaicking(first_ds_intersection,
                                   second_ds_intersection)
        top = first_dataset.where(
            first_dataset.y > second_bounds[3], drop=True)
        if len(bottom.y) == 0:
            return xr.concat([intersection, top], dim="y")
        return xr.concat([bottom, intersection, top], dim="y")

    if IntersectionType.RIGHT in intersection_types:
        left = first_dataset.where(
            first_dataset.x < second_bounds[0], drop=True)
        first_ds_intersection = first_dataset.where(
            first_dataset.x >= second_bounds[0], drop=True)
        second_ds_intersection = second_dataset.where(
            second_dataset.x <= first_bounds[2], drop=True)
        intersection = _mosaicking(first_ds_intersection,
                                   second_ds_intersection)
        right = second_dataset.where(
            second_dataset.x > first_bounds[2], drop=True)
        if len(right.x) == 0:
            return xr.concat([left, intersection], dim="x")
        return xr.concat([left, intersection, right], dim="x")

    if IntersectionType.TOP in intersection_types:
        bottom = first_dataset.where(
            first_dataset.y < second_bounds[1], drop=True)
        first_ds_intersection = first_dataset.where(
            first_dataset.y >= second_bounds[1], drop=True)
        second_ds_intersection = second_dataset.where(
            second_dataset.y <= first_bounds[3], drop=True)
        intersection = _mosaicking(first_ds_intersection,
                                   second_ds_intersection)
        top = second_dataset.where(
            second_dataset.y > first_bounds[3], drop=True)
        if len(top.y) == 0:
            return xr.concat([bottom, intersection], dim="y")
        return xr.concat([bottom, intersection, top], dim="y")
