import abc
from dataclasses import dataclass
from typing import Dict

import rasterio
import xarray as xr
from shapely.geometry import Polygon

from models.raster import Raster
from utils.xarray import getChunkShape
from utils.enums import ChunkingStrategy as CStrat


@dataclass
class AbstractRasterArchive(abc.ABC):
    bandsToExtract: Dict[str, str]
    productTime: int
    targetResolution: float
    rasterTimestamp: int

    # Loosely inspired from
    # https://gist.github.com/lucaswells/fd2fd73c513872966c1a0257afee1887
    def buildZarr(self, zarrPath, targetProjection: str,
                  polygon: Polygon = None, chunkMbs=1) -> xr.Dataset:
        """
        Build a chunked and compressed zarr from raster files.

        Parameters
        ----------
        zarrPath : str
            Path to final zarr file with all desired bands
        polygon: Polygon, optional
            Polygon representing the ROI
        chunk_mbs : float, optional
            Desired size (MB) of chunks in zarr file
        """

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
                    zarrPath, self.productTime,
                    self.rasterTimestamp, chunkMbs=chunkMbs)

                # Retrieve the most precise axis for future interpolation
                if raster.width > maxWidth:
                    maxWidth = raster.width
                    xGrid = xr.open_zarr(zarrStore).get("x")
                if raster.height > maxHeight:
                    maxHeight = raster.height
                    yGrid = xr.open_zarr(zarrStore).get("y")

                zarrs.append(zarrStore)
                metadata = raster.metadata

        # Retrieve the zarr stores as xarray objects that are on a same grid
        commonGrid = xr.Dataset({"x": xGrid, "y": yGrid})
        allZarrs = []
        for zarrStore in zarrs:
            xrZarr = xr.open_zarr(zarrStore)
            if xrZarr.dims["x"] != maxWidth or xrZarr.dims["y"] != maxHeight:
                chunkShape = getChunkShape(xrZarr.dims, CStrat.SPINACH)
                xrZarr = xrZarr.interp_like(commonGrid) \
                               .chunk(chunkShape)
            allZarrs.append(xrZarr)
        del zarrs

        # Merge all bands and remove temporary zarrs
        mergedBands: xr.Dataset = xr.merge(allZarrs)
        return mergedBands.assign_attrs(metadata)
