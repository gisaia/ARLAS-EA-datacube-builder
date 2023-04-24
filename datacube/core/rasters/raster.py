import math
import os.path as path

import numpy as np
import zarr
from rasterio.coords import BoundingBox
from rasterio.crs import CRS
from rasterio.io import DatasetReader
from rasterio.mask import mask
from rasterio.transform import IDENTITY, from_gcps
from rasterio.warp import (Resampling, calculate_default_transform, reproject,
                           transform_bounds)
from shapely.geometry import Polygon

from datacube.core.geo.utils import project_polygon
from datacube.core.geo.xarray import get_chunk_shape
from datacube.core.models.enums import ChunkingStrategy as CStrat


class Raster:

    def __init__(self, band: str, raster_reader: DatasetReader,
                 target_projection, polygon: Polygon):
        self.band = band
        self.dtype = raster_reader.dtypes[0].lower()
        self.crs = target_projection
        self.src_crs = raster_reader.crs

        # Extract the ROI in local referential
        if self.src_crs is None:
            self.src_crs = CRS.from_epsg(4326)
        local_proj_polygon = project_polygon(
                polygon, target_projection, self.src_crs)

        # Some raster files are not georeferenced with transform but with GCP
        if raster_reader.transform == IDENTITY:
            gcps = raster_reader.get_gcps()[0]
            ul = gcps[0]
            end_of_row = math.ceil(raster_reader.bounds.right / gcps[1].col)
            ur = gcps[end_of_row]
            ll = gcps[- 1 - end_of_row]
            lr = gcps[-1]

            raster_reader.transform = from_gcps([ul, ur, ll, lr])

        self.raster_data, src_transform = mask(
            raster_reader, [local_proj_polygon], crop=True)

        self.raster_data: np.ndarray = np.squeeze(self.raster_data)

        self.width = self.raster_data.shape[1]
        self.height = self.raster_data.shape[0]

        # Find the new bounding box of the data
        self.src_bounds = raster_reader.bounds
        raster_polygon = Polygon([
                (self.src_bounds.left, self.src_bounds.bottom),
                (self.src_bounds.right, self.src_bounds.bottom),
                (self.src_bounds.right, self.src_bounds.top),
                (self.src_bounds.left, self.src_bounds.top),
                (self.src_bounds.left, self.src_bounds.bottom)])

        intersection_bounds = local_proj_polygon.intersection(
            raster_polygon).bounds
        self.bounds = BoundingBox(*intersection_bounds)

        # Project the raster in the target projection
        self.transform, self.width, self.height = calculate_default_transform(
            self.src_crs, target_projection,
            self.width, self.height, *self.bounds)

        self.bounds = transform_bounds(
            self.src_crs, target_projection, *self.bounds)

        projected_raster_data = np.zeros((self.height, self.width))

        reproject(source=self.raster_data,
                  destination=projected_raster_data,
                  src_crs=self.src_crs,
                  src_nodata=raster_reader.nodata,
                  src_transform=src_transform,
                  dst_crs=target_projection,
                  dst_nodata=None,
                  dst_transform=self.transform,
                  resampling=Resampling.nearest)
        self.raster_data = projected_raster_data

        self.metadata = {}

    def create_zarr_dir(self, zarr_root_path: str,
                        product_timestamp: int,
                        raster_timestamp: int) -> zarr.DirectoryStore:

        store = zarr.DirectoryStore(path.join(zarr_root_path, self.band))

        xmin, ymin, xmax, ymax = self.bounds
        x = zarr.create(
            shape=(self.width,),
            dtype='float32',
            store=store,
            overwrite=True,
            path="x"
        )
        x[:] = np.arange(xmin, xmax, (xmax - xmin) / self.width)
        x.attrs['_ARRAY_DIMENSIONS'] = ['x']

        y = zarr.create(
            shape=(self.height,),
            dtype='float32',
            store=store,
            overwrite=True,
            path="y"
        )
        y[:] = np.arange(ymin, ymax, (ymax - ymin) / self.height)
        y.attrs['_ARRAY_DIMENSIONS'] = ['y']

        t = zarr.create(
            shape=(1,),
            dtype="int",
            store=store,
            overwrite=True,
            path="t"
        )
        t[:] = [raster_timestamp]
        t.attrs['_ARRAY_DIMENSIONS'] = ['t']

        chunk_shape = get_chunk_shape(
            {"x": self.width, "y": self.height, "t": 1}, CStrat.SPINACH)

        # Create zarr array for each band required
        zarray = zarr.create(
            shape=(self.width, self.height, 1),
            chunks=tuple(chunk_shape.values()),
            dtype=self.dtype,
            store=store,
            overwrite=True,
            path=self.band
        )

        # Add band metadata to the zarr file
        zarray.attrs['_ARRAY_DIMENSIONS'] = ['x', 'y', 't']
        self.metadata['product_timestamp'] = product_timestamp

        zarray[:, :, 0] = np.flip(np.transpose(self.raster_data), 1)

        # Consolidate the metadata into a single .zmetadata file
        zarr.consolidate_metadata(store)

        return store
