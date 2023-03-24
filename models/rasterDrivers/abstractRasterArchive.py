import abc
from dataclasses import dataclass
from typing import Dict

import os.path as path
import os
import shutil
import rasterio
import xarray as xr
from shapely.geometry import Polygon

from models.objectStoreDrivers.abstractObjectStore import AbstractObjectStore
from models.raster import Raster

from utils.xarray import getChunkShape
from utils.enums import ChunkingStrategy as CStrat

TMP = "tmp"
FINAL = "final"


@dataclass
class AbstractRasterArchive(abc.ABC):
    bandsToExtract: Dict[str, str]
    productTime: int
    target_resolution: float
    rasterTimestamp: int

    @abc.abstractmethod
    def __init__(self, objectStore: AbstractObjectStore, rasterURI: str,
                 bands: Dict[str, str], target_resolution: int,
                 rasterTimestamp: int, zipExtractPath: str):
        pass

    # Loosely inspired from
    # https://gist.github.com/lucaswells/fd2fd73c513872966c1a0257afee1887
    def buildZarr(self, zarrRootPath, target_projection: str,
                  polygon: Polygon = None) -> str:
        """
        Build a chunked and zarr from raster files.

        Parameters
        ----------
        zarrRootPath : str
            The root path where the temporary and final zarrs will be created
        polygon: Polygon, optional
            Polygon representing the ROI
        chunk_mbs : float, optional
            Desired size (MB) of chunks in zarr file
        """
        zarrTmpRootPath = path.join(zarrRootPath, TMP)

        # Open all rasters to get the zarr stores
        zarrs = []
        maxWidth = 0
        maxHeight = 0

        # Create all the zarr files/stores
        # Finds the most precise grid for the zarrs
        for band, rasterPath in self.bandsToExtract.items():
            with rasterio.open(rasterPath, "r+") as rasterReader:
                # Create Raster object
                raster = Raster(band, rasterReader, target_projection, polygon)

                # Create zarr store
                zarrStore = raster.createZarrStore(
                    zarrTmpRootPath, self.productTime,
                    self.rasterTimestamp)

                # Retrieve the most precise axis for future interpolation
                if raster.width > maxWidth:
                    maxWidth = raster.width
                    with xr.open_zarr(zarrStore) as ds:
                        xGrid = ds.get("x")
                if raster.height > maxHeight:
                    maxHeight = raster.height
                    with xr.open_zarr(zarrStore) as ds:
                        yGrid = ds.get("y")

                zarrs.append(zarrStore)
                metadata = raster.metadata

        # Retrieve the zarr stores as xarray objects that are on a same grid
        commonGrid = xr.Dataset({"x": xGrid, "y": yGrid})
        mergedBands: xr.Dataset = None
        for zarrStore in zarrs:
            with xr.open_zarr(zarrStore) as xrZarr:
                if xrZarr.dims["x"] != maxWidth \
                        or xrZarr.dims["y"] != maxHeight:
                    chunkShape = getChunkShape(xrZarr.dims, CStrat.SPINACH)
                    xrZarr = xrZarr.interp_like(commonGrid) \
                                   .chunk(chunkShape)
                # If raster is Sentinel2, replace negative values with NaN
                if type(self).PRODUCT_TYPE.source == "Sentinel2":
                    for band in xrZarr.data_vars:
                        xrZarr[band] = xrZarr[band].where(xrZarr[band] >= 0)
                if mergedBands is None:
                    mergedBands = xrZarr
                else:
                    mergedBands = xr.merge((mergedBands, xrZarr))

        # Merge all bands and remove temporary zarrs
        mergedBands.assign_attrs(metadata) \
                   .to_zarr(path.join(zarrRootPath, FINAL), mode="w") \
                   .close()

        # Clean up the temporary files created
        del zarrs
        del mergedBands
        if os.path.exists(zarrTmpRootPath) and os.path.isdir(zarrTmpRootPath):
            shutil.rmtree(zarrTmpRootPath)

        return path.join(zarrRootPath, FINAL)
