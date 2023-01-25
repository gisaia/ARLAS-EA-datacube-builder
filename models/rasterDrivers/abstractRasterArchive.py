import abc
from dataclasses import dataclass
from typing import Dict

import os.path as path
import os
import shutil
import rasterio
import xarray as xr
from shapely.geometry import Polygon

from models.raster import Raster
from utils.xarray import getChunkShape
from utils.enums import ChunkingStrategy as CStrat

TMP = "tmp"
FINAL = "final"


@dataclass
class AbstractRasterArchive(abc.ABC):
    bandsToExtract: Dict[str, str]
    productTime: int
    targetResolution: float
    rasterTimestamp: int

    # Loosely inspired from
    # https://gist.github.com/lucaswells/fd2fd73c513872966c1a0257afee1887
    def buildZarr(self, zarrRootPath, targetProjection: str,
                  polygon: Polygon = None, chunkMbs=1) -> str:
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
            with rasterio.open(rasterPath) as rasterReader:
                # Create Raster object
                raster = Raster(band, rasterReader, targetProjection, polygon)

                # Create zarr store
                zarrStore = raster.createZarrStore(
                    zarrTmpRootPath, self.productTime,
                    self.rasterTimestamp, chunkMbs=chunkMbs)

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
