#!/usr/bin/python3
from typing import List

import rasterio
from rasterio.io import DatasetReader
from rasterio.windows import Window
from rasterio.mask import mask
from rasterio.coords import BoundingBox

import zarr
import numpy as np

from shapely.geometry import Polygon

# inspired by https://gist.github.com/lucaswells/fd2fd73c513872966c1a0257afee1887
def convert(raster_filepath, zarr_filepath, polygon:Polygon=None, chunk_mbs=1):
    """
    Converts raster file to chunked and compressed zarr array.

    Parameters
    ----------
    raster_filepath : string
        Path and filename of input raster
    chunk_mbs : float, optional
        Desired size (MB) of chunks in zarr file
    """

    # Open the raster file
    raster = rasterio.open(raster_filepath)

    # Extract metadata we need for initializing the zarr array
    dtype = raster.dtypes[0].lower()
    bounds = raster.bounds
    crs = raster.crs.to_string()

    if polygon:
        rasterData, transform = extract(raster, [polygon])
        rasterData = np.squeeze(rasterData)

        width = rasterData.shape[1]
        height = rasterData.shape[0]

        # Find the new bounding box of the data
        rasterPolygon = Polygon([
                (bounds.left, bounds.bottom), 
                (bounds.right, bounds.bottom), 
                (bounds.right, bounds.top), 
                (bounds.left, bounds.top), 
                (bounds.left, bounds.bottom)])

        intersectionBounds = polygon.intersection(rasterPolygon).bounds
        bounds = BoundingBox(intersectionBounds[0], intersectionBounds[1], intersectionBounds[2], intersectionBounds[3])
    else:
        rasterData = raster.read(1)
        width = raster.width
        height = raster.height
        transform = raster.transform

    # Specify the number of bytes for common raster
    # datatypes so we can compute chunk shape
    dtype_bytes = {
        'byte'     : 1.,
        'uint16'   : 2.,
        'int16'    : 2.,
        'uint32'   : 4.,
        'int32'    : 4.,
        'float32'  : 4.,
        'float64'  : 8.,
    }

    # Compute the chunk shape
    chunk_shape = (int((chunk_mbs * 1e6/dtype_bytes[dtype])**0.5),)*2 #TODO: chunk size is not the correct one in the end

    # Create zarr store
    store = zarr.DirectoryStore(zarr_filepath)

    xmin, ymin, xmax, ymax = bounds

    x = zarr.create(
        shape=(width,),
        dtype='float32',
        store=store,
        overwrite=True,
        path="x"
    )
    x[:] = np.arange(xmin, xmax, (xmax-xmin)/width)
    x.attrs['_ARRAY_DIMENSIONS'] = ['x']

    y = zarr.create(
        shape=(height,),
        dtype='float32',
        store=store,
        overwrite=True,
        path="y"
    )
    y[:] = np.arange(ymin, ymax, (ymax-ymin)/height)
    y.attrs['_ARRAY_DIMENSIONS'] = ['y']

    for k in raster.indexes:
        # Create zarr array for each band required
        zarray = zarr.create(
            shape=(width, height),
            chunks=chunk_shape,
            dtype=dtype,
            store=store,
            overwrite=True,
            path=k #TODO: replace k with the name of the band
        )

        # Let's add the metadata to the zarr file
        zarray.attrs['width'] = width
        zarray.attrs['height'] = height
        zarray.attrs['dtype'] = dtype
        zarray.attrs['bounds'] = bounds
        zarray.attrs['transform'] = transform
        zarray.attrs['crs'] = crs
        zarray.attrs['_ARRAY_DIMENSIONS'] = ['x', 'y']

        zarray[:] = np.flip(np.transpose(rasterData), 1)
    
    # Close the raster dataset; no need to close the zarr file
    raster.close()

    # Consolidate the metadata into a single .zmetadata file
    zarr.consolidate_metadata(store)

def extract(raster:DatasetReader, polygons:List[Polygon]):
    return mask(raster, polygons, crop=True)

if __name__ == "__main__":
    RASTER_FILE = "./data/soilClassificationwithMachineLearningwithPythonScikitLearn/S2B_MSIL1C_20200917T151709_N0209_R125_T18LUM_20200917T203629.SAFE/GRANULE/L1C_T18LUM_A018455_20200917T151745/IMG_DATA/T18LUM_20200917T151709_B01.jp2"
    ZARR_FILE = "./output/zarr/test"

    polygon = Polygon([(383700.0, 8651200.0), (397400.0, 8651200.0), (397400.0, 8642300.0), (383700.0, 8642300.0), (383700.0, 8651200.0)])

    convert(RASTER_FILE, ZARR_FILE, polygon)