import os.path as path
import numpy as np
import zarr
import math
from shapely.geometry import Polygon

from rasterio.coords import BoundingBox
from rasterio.io import DatasetReader
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, \
    Resampling, transform_bounds
from rasterio.transform import IDENTITY, from_gcps


from utils.geometry import project_polygon
from utils.xarray import get_chunk_shape
from utils.enums import ChunkingStrategy as CStrat


class Raster:

    def __init__(self, band: str, raster_reader: DatasetReader,
                 target_projection, polygon: Polygon):
        self.band = band
        self.dtype = raster_reader.dtypes[0].lower()
        self.crs = target_projection

        # Extract the ROI in local referential
        if raster_reader.crs is None:
            raster_reader.crs = "EPSG:4326"
        local_proj_polygon = project_polygon(
                polygon, target_projection, raster_reader.crs)

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
        bounds = raster_reader.bounds
        raster_polygon = Polygon([
                (bounds.left, bounds.bottom),
                (bounds.right, bounds.bottom),
                (bounds.right, bounds.top),
                (bounds.left, bounds.top),
                (bounds.left, bounds.bottom)])

        intersection_bounds = local_proj_polygon.intersection(
            raster_polygon).bounds
        self.bounds = BoundingBox(*intersection_bounds)

        # Project the raster in the target projection
        self.transform, self.width, self.height = calculate_default_transform(
            raster_reader.crs, target_projection,
            self.width, self.height, *self.bounds)

        self.bounds = transform_bounds(
            raster_reader.crs, target_projection, *self.bounds)

        projected_raster_data = np.zeros((self.height, self.width))

        reproject(source=self.raster_data,
                  destination=projected_raster_data,
                  src_crs=raster_reader.crs,
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
