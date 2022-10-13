#!/usr/bin/python3

import rasterio
from rasterio.windows import Window
import zarr
import numpy as np

# inspired by https://gist.github.com/lucaswells/fd2fd73c513872966c1a0257afee1887
def convert(raster_filepath, zarr_filepath, chunk_mbs=1):
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
    width = raster.width
    height = raster.height
    n_bands = raster.count
    dtype = raster.dtypes[0].lower()

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

    xmin, ymin, xmax, ymax = raster.bounds

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
        zarray.attrs['count'] = n_bands
        zarray.attrs['dtype'] = dtype
        zarray.attrs['bounds'] = raster.bounds
        zarray.attrs['transform'] = raster.transform
        zarray.attrs['crs'] = raster.crs.to_string()
        zarray.attrs['_ARRAY_DIMENSIONS'] = ['x', 'y']

        # Now we'll read and write the data according to the chuck size to prevent memory saturation
        for xstart in range(0, width+chunk_shape[0], chunk_shape[0]):
            if xstart > width:
                continue
            xend = min(xstart + chunk_shape[0], width)
            for ystart in range(0, height+chunk_shape[1], chunk_shape[1]):
                if ystart > height:
                    continue
                yend = min(ystart + chunk_shape[1], height)

                print('Chunk')
                print(f'column {xstart} to {xend} out of {width}')
                print(f'line {ystart} to {yend} out of {height}\n')

                data = raster.read(k, window=Window(xstart, ystart, xend - xstart, yend - ystart))
                zarray[xstart:xend, ystart:yend] = np.transpose(data)
    
    # Close the raster dataset; no need to close the zarr file
    raster.close()

    # Consolidate the metadata into a single .zmetadata file
    zarr.consolidate_metadata(store)