#!/usr/bin/python3
import base64
import os
import os.path as path
import shutil
import time
import traceback
from urllib.parse import urlparse

import mr4mp
import numpy as np
import xarray as xr
from shapely.geometry import Point

from datacube.core.cache.cache_manager import CacheManager
from datacube.core.geo.utils import complete_grid
from datacube.core.geo.xarray import (get_bounds, get_chunk_shape,
                                      merge_datasets)
from datacube.core.logging.logger import CustomLogger as Logger
from datacube.core.metadata import create_datacube_metadata
from datacube.core.models.cubeBuildResult import CubeBuildResult
from datacube.core.models.enums import ChunkingStrategy as CStrat
from datacube.core.models.exception import (DownloadError, MosaickingError,
                                            UploadError)
from datacube.core.models.request.cubeBuild import ExtendedCubeBuildRequest
from datacube.core.pivot.format import pivot_format_datacube
from datacube.core.storage.utils import (create_input_storage,
                                         get_mapper_output, write_bytes)
from datacube.core.utils import (get_eval_formula, get_product_bands,
                                 get_raster_driver)
from datacube.core.visualisation.preview import (create_preview_b64,
                                                 create_preview_b64_cmap,
                                                 prepare_visualisation)

TMP_DIR = "tmp/"
LOGGER = Logger.get_logger()
CACHE = {}


def __download(input: tuple[ExtendedCubeBuildRequest, int, int]) \
        -> dict[float, list[str]]:
    """
    Builds a zarr corresponding to the requested bands for
    the raster file 'file_idx' in the group 'group_idx'
    """
    request = input[0]
    group_idx = input[1]
    file_idx = input[2]

    try:
        # Retrieve from the request the important information
        raster_file = request.composition[group_idx].rasters[file_idx]
        timestamp = request.composition[group_idx].timestamp

        input_storage = create_input_storage(
            urlparse(raster_file.path).scheme)

        LOGGER.info(f"[group-{group_idx}:file-{file_idx}] Extracting bands")
        # Depending on archive type, extract desired data
        raster_archive = get_raster_driver(raster_file.type)(
            input_storage, raster_file.path,
            get_product_bands(request, raster_file.type),
            request.target_resolution,
            timestamp, TMP_DIR)

        LOGGER.info(f"[group-{group_idx}:file-{file_idx}] Building ZARR")
        # Build the zarr dataset and add it to its group's list
        zarr_root_path = path.join(TMP_DIR, f"{request.datacube_path}",
                                   f'{group_idx}/{file_idx}')
        zarr_path = raster_archive.build_zarr(zarr_root_path,
                                              request.target_projection,
                                              polygon=request.roi_polygon)
        CacheManager.put_raster(raster_archive)

        grouped_datasets: dict[int, list[str]] = {timestamp: [zarr_path]}
        return grouped_datasets
    except Exception as e:
        LOGGER.error(f"[group-{group_idx}:file-{file_idx}]")
        traceback.print_exc()
        if isinstance(e, DownloadError):
            raise e
        raise DownloadError(title=f"[group-{group_idx}:file-{file_idx}]",
                            detail=e.args[0])


def merge_download(result_a: dict[int, list[str]],
                   result_b: dict[int, list[str]]) \
                   -> dict[int, list[str]]:
    """
    Merge the results of the download method in a mapreduce process
    """
    for timestamp in list(result_b.keys()):
        if timestamp in list(result_a.keys()):
            result_a[timestamp].extend(result_b[timestamp])
        else:
            result_a[timestamp] = result_b[timestamp]
    return result_a


def __mosaicking(merge_input) -> xr.Dataset:
    list_ds_adress = merge_input[0]
    lon = merge_input[1]
    lat = merge_input[2]
    lon_step = merge_input[3]
    lat_step = merge_input[4]

    merged_dataset = None
    for ds_adress in list_ds_adress:
        # Interpolate the granule with new grid on its extent
        with xr.open_zarr(ds_adress) as dataset:
            bounds = get_bounds(dataset)
            granule_grid = {}
            granule_grid["x"] = lon[(lon[:] >= bounds[0])
                                    & (lon[:] <= bounds[2])]
            granule_grid["y"] = lat[(lat[:] >= bounds[1])
                                    & (lat[:] <= bounds[3])]
            granule_grid["x"], granule_grid["y"] = complete_grid(
                granule_grid["x"], granule_grid["y"],
                lon_step, lat_step, bounds)
            dims = {"x": len(granule_grid["x"]),
                    "y": len(granule_grid["y"]), "t": 1}

            merged_dataset = merge_datasets(
                merged_dataset,
                dataset.interp_like(
                    xr.Dataset(granule_grid), method="nearest")
                .chunk(get_chunk_shape(dims, CStrat.SPINACH)))

    return merged_dataset


def __merge_mosaicking(mosaick_a: xr.Dataset,
                       mosaick_b: xr.Dataset) -> xr.Dataset:
    return xr.combine_by_coords(
        (mosaick_a, mosaick_b), combine_attrs="override")


def build_datacube(request: ExtendedCubeBuildRequest):
    grouped_datasets: dict[int, list[str]] = {}

    center_granule_idx = {"group": int, "index": int}
    xmin, ymin, xmax, ymax = np.inf, np.inf, -np.inf, -np.inf
    roi_centroid: Point = request.roi_polygon.centroid
    min_distance = np.inf

    zarr_root_path = path.join(TMP_DIR, request.datacube_path)
    # Remove trailing "/" if present
    zarr_root_path = zarr_root_path if zarr_root_path[-1] != "/" \
        else zarr_root_path[:-2]

    # Generate the iterable of all files to download
    download_iter = []
    for group_idx in range(len(request.composition)):
        for idx in range(len(request.composition[group_idx].rasters)):
            download_iter.append((request, group_idx, idx))

    # Download parallely the groups of bands of each file
    try:
        with mr4mp.pool(close=True) as pool:
            grouped_datasets = pool.mapreduce(
                __download, merge_download, download_iter)
    except DownloadError as e:
        raise e

    for timestamp, ds_list in grouped_datasets.items():
        for idx, ds_adress in enumerate(ds_list):
            # Find the centermost granule based on ROI and max bounds
            with xr.open_zarr(ds_adress) as dataset:
                ds_bounds = get_bounds(dataset)
                granule_center = Point((ds_bounds[0] + ds_bounds[2])/2,
                                       (ds_bounds[1] + ds_bounds[3])/2)
                if roi_centroid.distance(granule_center) < min_distance:
                    min_distance = roi_centroid.distance(granule_center)
                    center_granule_idx["group"] = timestamp
                    center_granule_idx["index"] = idx

                # Update the extent of the datacube
                xmin = min(xmin, ds_bounds[0])
                ymin = min(ymin, ds_bounds[1])
                xmax = max(xmax, ds_bounds[2])
                ymax = max(ymax, ds_bounds[3])

    LOGGER.info("Building datacube from the ZARRs")
    # If there is more than one file requested
    if not (len(request.composition) == 1 and
            len(request.composition[0].rasters) == 1):
        try:
            # Generate a grid based on the step size of the center granule
            # extending the center of the roi
            with xr.open_zarr(grouped_datasets[center_granule_idx["group"]][
                        center_granule_idx["index"]]) as center_granule_ds:
                lon_step = float(center_granule_ds.get("x").diff("x").mean()
                                 .values.tolist())
                lat_step = float(center_granule_ds.get("y").diff("y").mean()
                                 .values.tolist())

                lon, lat = complete_grid([roi_centroid.x], [roi_centroid.y],
                                         lon_step, lat_step,
                                         (xmin, ymin, xmax, ymax))

            # For each time bucket, create a mosaick of the datasets
            timestamps = list(grouped_datasets.keys())
            timestamps.sort()

            mosaicking_iter = []
            for t in timestamps:
                mosaicking_iter.append([grouped_datasets[t], lon, lat,
                                       lon_step, lat_step])

            with mr4mp.pool(close=True) as pool:
                datacube = pool.mapreduce(__mosaicking, __merge_mosaicking,
                                          mosaicking_iter)

        except Exception as e:
            LOGGER.error(e)
            traceback.print_exc()
            raise MosaickingError(detail=e.args[0])
    else:
        first_ds = grouped_datasets[list(grouped_datasets.keys())[0]][0]
        with xr.open_zarr(first_ds) as ds:
            datacube = ds
            lon_step = float(datacube.get("x").diff("x").mean()
                             .values.tolist())
            lat_step = float(datacube.get("y").diff("y").mean()
                             .values.tolist())

    # Compute the bands requested from the product bands
    for band in request.bands:
        datacube[band.name] = eval(
            get_eval_formula(band.expression, request.aliases))
        if band.min is not None and band.max is not None:
            datacube[band.name] = datacube[band.name].clip(band.min, band.max)

    # Keep just the bands requested
    requested_bands = [band.name for band in request.bands]
    datacube = datacube[requested_bands]

    # Add relevant datacube metadata
    metadata = create_datacube_metadata(request, datacube, lon_step, lat_step)
    datacube.attrs.update(metadata.dict(exclude_unset=True, by_alias=True))
    datacube.attrs.update({"description": request.description})

    if request.pivot_format:
        # Write datacube in tmp dir
        final_datacube = f"{zarr_root_path}_{str(time.time())}"
        datacube.chunk(get_chunk_shape(
                datacube.dims, request.chunking_strategy)) \
            .to_zarr(final_datacube, mode="w") \
            .close()

        # Format datacube to pivot
        pivot_path, preview_file_name, preview = pivot_format_datacube(
            request, final_datacube, metadata)
        shutil.rmtree(final_datacube)

        LOGGER.info("Writing datacube in pivot format to storage")
        try:
            with open(pivot_path, 'rb') as ftar:
                product_url = write_bytes(pivot_path.split("/")[-1],
                                          ftar.read())
                preview_url = path.join(product_url, preview_file_name)
            os.remove(pivot_path)

        except Exception as e:
            LOGGER.error(e)
            traceback.print_exc()
            raise UploadError(detail=f"Datacube: {e.args[0]}")

    else:
        LOGGER.info("Writing datacube to storage")
        try:
            product_url, mapper = get_mapper_output(request.datacube_path)

            datacube.chunk(get_chunk_shape(
                    datacube.dims, request.chunking_strategy)) \
                .to_zarr(mapper, mode="w") \
                .close()

        except Exception as e:
            LOGGER.error(e)
            traceback.print_exc()
            raise UploadError(detail=f"Datacube: {e.args[0]}")

        preview_file_name = f"{request.datacube_path}.jpg"

        # Creating preview
        LOGGER.info("Preparing datacube for preview generation")
        coarsed_datacube, clip_values = prepare_visualisation(
            datacube, list(datacube.attrs["dc3:preview"].values()))

        preview_path = f'{zarr_root_path}.jpg'
        if len(datacube.attrs["dc3:preview"]) == 3:
            preview = create_preview_b64(coarsed_datacube, request.rgb,
                                         preview_path, clip_values)
        else:
            preview = create_preview_b64_cmap(
                coarsed_datacube, datacube.attrs["dc3:preview"],
                preview_path, clip_values)
        LOGGER.info("Preview generated")

        LOGGER.info("Uploading preview to storage")
        try:
            preview_url = write_bytes(preview_file_name,
                                      base64.b64decode(preview))
        except Exception as e:
            LOGGER.error(e)
            traceback.print_exc()
            raise UploadError(detail=f"Preview: {e.args[0]}")

    # Clean up the files created
    del datacube
    if path.exists(zarr_root_path) and path.isdir(zarr_root_path):
        shutil.rmtree(zarr_root_path)

    return CubeBuildResult(
        product_url=product_url,
        preview_url=preview_url,
        preview=preview)
