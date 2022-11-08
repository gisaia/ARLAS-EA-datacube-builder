import abc
from typing import Dict

import numpy as np
import rasterio
import xarray as xr
from shapely.geometry import Polygon

from models.raster import Raster, getChunkSize


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
        dtype = ""

        # Create all the zarr files/stores
        # Finds the most precise grid for the zarrs
        for band, rasterPath in self.bandsToExtract.items():
            with rasterio.open(rasterPath) as rasterReader:
                # Create Raster object
                raster = Raster(band, rasterReader, targetProjection, polygon)
                dtype = raster.dtype

                # Create zarr store
                zarrStore = raster.createZarrStore(
                    zarrPath, self.productTime,
                    self.rasterTimestamp, chunkMbs=chunkMbs)

                # Retrieve the most precise axis for future interpolation
                if raster.width > maxWidth:
                    maxWidth = raster.width
                    xmin, _, xmax, _ = raster.bounds
                if raster.height > maxHeight:
                    maxHeight = raster.height
                    _, ymin, _, ymax = raster.bounds

                zarrs.append(zarrStore)

        # Retrieve the zarr stores as xarray objects that are on a same grid
        interpDataset = xr.Dataset({
            "x": np.arange(xmin, xmax, self.targetResolution),
            "y": np.arange(ymin, ymax, self.targetResolution)})
        allZarrs = []
        for zarrStore in zarrs:
            xrZarr = xr.open_zarr(zarrStore)
            if xrZarr.dims["x"] != maxWidth or xrZarr.dims["y"] != maxHeight:
                xrZarr = xrZarr.interp_like(interpDataset) \
                            .chunk(getChunkSize(dtype, chunkMbs))
            allZarrs.append(xrZarr)
        del zarrs

        # Merge all bands and remove temporary zarrs
        return xr.merge(allZarrs)
