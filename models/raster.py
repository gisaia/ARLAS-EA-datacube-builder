import numpy as np
import zarr
from rasterio.coords import BoundingBox
from rasterio.io import DatasetReader
from rasterio.mask import mask
from rasterio.transform import AffineTransformer
from shapely.geometry import Polygon

DTYPE_BYTES = {
    'byte': 1,
    'uint16': 2,
    'int16': 2,
    'uint32': 4,
    'int32': 4,
    'float32': 4,
    'float64': 8,
}


def getChunkSize(dtype: str, chunkMbs: float):
    return int((chunkMbs * 1e6/DTYPE_BYTES[dtype])**0.5)


class Raster:
    band: str
    rasterData: np.array
    width: int
    height: int
    bounds: BoundingBox
    transform: AffineTransformer
    dtype: str
    crs: str

    def __init__(self, band: str, rasterReader: DatasetReader,
                 polygon: Polygon = None):
        self.band = band
        self.dtype = rasterReader.dtypes[0].lower()
        self.crs = rasterReader.crs.to_string()

        if polygon:
            self.rasterData, self.transform = mask(rasterReader,
                                                   [polygon], crop=True)
            self.rasterData = np.squeeze(self.rasterData)

            self.width = self.rasterData.shape[1]
            self.height = self.rasterData.shape[0]

            # Find the new bounding box of the data
            bounds = rasterReader.bounds
            rasterPolygon = Polygon([
                    (bounds.left, bounds.bottom),
                    (bounds.right, bounds.bottom),
                    (bounds.right, bounds.top),
                    (bounds.left, bounds.top),
                    (bounds.left, bounds.bottom)])

            intersectionBounds = polygon.intersection(rasterPolygon).bounds
            self.bounds = BoundingBox(intersectionBounds[0],
                                      intersectionBounds[1],
                                      intersectionBounds[2],
                                      intersectionBounds[3])
        else:
            self.rasterData = rasterReader.read(1)
            self.width = rasterReader.width
            self.height = rasterReader.height
            self.bounds = rasterReader.bounds
            self.transform = rasterReader.transform

    def createZarrFile(self,
                       zarrRootPath: str, chunkMbs=1) -> zarr.DirectoryStore:

        store = zarr.DirectoryStore(f"{zarrRootPath}/{self.band}")

        chunkShape = (getChunkSize(self.dtype, chunkMbs),)*2
        # TODO: chunk size is not the correct one in the end

        xmin, ymin, xmax, ymax = self.bounds
        x = zarr.create(
            shape=(self.width,),
            dtype='float32',
            store=store,
            overwrite=True,
            path="x"
        )
        x[:] = np.arange(xmin, xmax, (xmax-xmin)/self.width)
        x.attrs['_ARRAY_DIMENSIONS'] = ['x']

        y = zarr.create(
            shape=(self.height,),
            dtype='float32',
            store=store,
            overwrite=True,
            path="y"
        )
        y[:] = np.arange(ymin, ymax, (ymax-ymin)/self.height)
        y.attrs['_ARRAY_DIMENSIONS'] = ['y']

        # Create zarr array for each band required
        zarray = zarr.create(
            shape=(self.width, self.height),
            chunks=chunkShape,
            dtype=self.dtype,
            store=store,
            overwrite=True,
            path=self.band
        )

        # Add band metadata to the zarr file
        zarray.attrs['width'] = self.width
        zarray.attrs['height'] = self.height
        zarray.attrs['dtype'] = self.dtype
        zarray.attrs['bounds'] = self.bounds
        zarray.attrs['transform'] = self.transform
        zarray.attrs['crs'] = self.crs
        zarray.attrs['_ARRAY_DIMENSIONS'] = ['x', 'y']

        zarray[:] = np.flip(np.transpose(self.rasterData), 1)

        # Consolidate the metadata into a single .zmetadata file
        zarr.consolidate_metadata(store)

        return store
