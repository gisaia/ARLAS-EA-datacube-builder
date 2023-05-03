import abc
import os
import os.path as path
import shutil
from dataclasses import dataclass

import rasterio
import xarray as xr
from pydantic import BaseModel, Field
from rasterio.coords import BoundingBox
from rasterio.crs import CRS
from shapely.geometry import Polygon

from datacube.core.geo.xarray import get_chunk_shape
from datacube.core.models.enums import ChunkingStrategy as CStrat
from datacube.core.models.request.rasterProductType import RasterType
from datacube.core.object_store.drivers.abstract import AbstractObjectStore
from datacube.core.rasters.raster import Raster

TMP = "tmp"
FINAL = "final"


class CachedAbstractRasterArchive(BaseModel):
    timestamp: int = Field()
    crs: str = Field()
    bottom: float = Field()
    right: float = Field()
    top: float = Field()
    left: float = Field()
    type: RasterType = Field()


@dataclass
class AbstractRasterArchive(abc.ABC):
    raster_timestamp: int
    raster_uri: str

    bands_to_extract: dict[str, str]
    product_time: int
    target_resolution: float
    src_bounds: BoundingBox = None
    src_crs: CRS = None

    @abc.abstractmethod
    def __init__(self, object_store: AbstractObjectStore, raster_uri: str,
                 bands: dict[str, str], target_resolution: int,
                 raster_timestamp: int, zip_extract_path: str):
        pass

    def set_raster_metadata(self, raster_uri: str, raster_timestamp: int):
        self.raster_uri = raster_uri
        self.raster_timestamp = raster_timestamp

    # Loosely inspired from
    # https://gist.github.com/lucaswells/fd2fd73c513872966c1a0257afee1887
    def build_zarr(self, zarr_root_path, target_projection: str,
                   polygon: Polygon = None) -> str:
        """
        Build a chunked and zarr from raster files.

        Parameters
        ----------
        zarr_root_path : str
            The root path where the temporary and final zarrs will be created
        polygon: Polygon, optional
            Polygon representing the ROI
        chunk_mbs : float, optional
            Desired size (MB) of chunks in zarr file
        """
        zarr_tmp_root_path = path.join(zarr_root_path, TMP)

        # Open all rasters to get the zarr stores
        zarrs = []
        max_width = 0
        max_height = 0

        # Create all the zarr files/stores
        # Finds the most precise grid for the zarrs
        for band, raster_path in self.bands_to_extract.items():
            with rasterio.open(raster_path, "r+") as raster_reader:
                # Create Raster object
                raster = Raster(band, raster_reader,
                                target_projection, polygon)

                self.src_bounds = raster.src_bounds
                self.src_crs = raster.src_crs

                # Create zarr store
                zarr_dir = raster.create_zarr_dir(
                    zarr_tmp_root_path, self.product_time,
                    self.raster_timestamp)

                # Retrieve the most precise axis for future interpolation
                if raster.width > max_width:
                    max_width = raster.width
                    with xr.open_zarr(zarr_dir) as ds:
                        xGrid = ds.get("x")
                if raster.height > max_height:
                    max_height = raster.height
                    with xr.open_zarr(zarr_dir) as ds:
                        yGrid = ds.get("y")

                zarrs.append(zarr_dir)
                metadata = raster.metadata

        # Retrieve the zarr stores as xarray objects that are on a same grid
        common_grid = xr.Dataset({"x": xGrid, "y": yGrid})
        merged_bands: xr.Dataset = None
        for zarr_dir in zarrs:
            with xr.open_zarr(zarr_dir) as xr_zarr:
                if xr_zarr.dims["x"] != max_width \
                        or xr_zarr.dims["y"] != max_height:
                    chunk_shape = get_chunk_shape(xr_zarr.dims, CStrat.SPINACH)
                    xr_zarr = xr_zarr.interp_like(common_grid) \
                                     .chunk(chunk_shape)
                # If raster is Sentinel2, replace negative values with NaN
                if type(self).PRODUCT_TYPE.source == "Sentinel2":
                    for band in xr_zarr.data_vars:
                        xr_zarr[band] = xr_zarr[band].where(xr_zarr[band] >= 0)
                if merged_bands is None:
                    merged_bands = xr_zarr
                else:
                    merged_bands = xr.merge((merged_bands, xr_zarr))

        # Merge all bands and remove temporary zarrs
        merged_bands.assign_attrs(metadata) \
                    .to_zarr(path.join(zarr_root_path, FINAL), mode="w") \
                    .close()

        # Clean up the temporary files created
        del zarrs
        del merged_bands
        if os.path.exists(zarr_tmp_root_path) and \
                os.path.isdir(zarr_tmp_root_path):
            shutil.rmtree(zarr_tmp_root_path)

        return path.join(zarr_root_path, FINAL)

    def cache_information(self) -> CachedAbstractRasterArchive:
        return CachedAbstractRasterArchive(
            timestamp=self.product_time,
            crs=self.src_crs.to_string(),
            bottom=self.src_bounds.bottom,
            right=self.src_bounds.right,
            top=self.src_bounds.top,
            left=self.src_bounds.left,
            type=type(self).PRODUCT_TYPE
        )
