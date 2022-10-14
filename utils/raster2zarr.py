#!/usr/bin/python3
import shutil
from typing import List

import numpy as np
import rasterio
import xarray as xr
from rasterio.io import DatasetReader
from rasterio.mask import mask
from shapely.geometry import Polygon

from models.raster import Raster, getChunkSize


# Loosely inspired from
# https://gist.github.com/lucaswells/fd2fd73c513872966c1a0257afee1887
def convert(bandsToExtract: List[str], zarrFilepath,
            polygon: Polygon = None, chunkMbs=1):
    """
    Converts raster file to chunked and compressed zarr array.

    Parameters
    ----------
    bandsToExtract : List[str]
        Paths to raster bands
    zarrFilepath : str
        Path to final zarr file with all bands
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
    # Finds the most precise grid to use it for the zarrs
    for band in bandsToExtract:
        with rasterio.open(band) as rasterReader:
            # Create Raster object
            raster = Raster(band[-7:-4], rasterReader, polygon)
            dtype = raster.dtype

            # Create zarr file
            zarrStore = raster.createZarrFile(
                zarrFilepath + "_tmp", chunkMbs=chunkMbs)

            # Retrieve the most precise axis to use for future interpolation
            if raster.width > maxWidth:
                maxWidth = raster.width
                xmin, _, xmax, _ = raster.bounds
                x = np.arange(xmin, xmax, (xmax-xmin)/raster.width)
            if raster.height > maxHeight:
                maxHeight = raster.height
                _, ymin, _, ymax = raster.bounds
                y = np.arange(ymin, ymax, (ymax-ymin)/raster.height)

            zarrs.append(zarrStore)

    # Retrieve the zarr stores as xarray objects that are on a same grid
    interpDataset = xr.Dataset({"x": x, "y": y})
    allZarrs = []
    for zarrStore in zarrs:
        xrZarr = xr.open_zarr(zarrStore)
        if xrZarr.dims["x"] != maxWidth or xrZarr.dims["y"] != maxHeight:
            xrZarr = xrZarr.interp_like(interpDataset) \
                           .chunk(getChunkSize(dtype, chunkMbs))
        allZarrs.append(xrZarr)
    del zarrs

    # Merge all bands and remove temporary zarrs
    xr.merge(allZarrs).to_zarr(zarrFilepath)
    shutil.rmtree(zarrFilepath + "_tmp")


def extract(raster: DatasetReader, polygons: List[Polygon]):
    return mask(raster, polygons, crop=True)
