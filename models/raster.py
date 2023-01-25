import os.path as path
import numpy as np
import zarr
from rasterio.coords import BoundingBox
from rasterio.io import DatasetReader
from rasterio.mask import mask
from shapely.geometry import Polygon
from rasterio.warp import calculate_default_transform, reproject, \
    Resampling, transform_bounds

from utils.geometry import projectPolygon
from utils.xarray import getChunkShape
from utils.enums import ChunkingStrategy as CStrat


class Raster:

    def __init__(self, band: str, rasterReader: DatasetReader,
                 targetProjection, polygon: Polygon = None):
        self.band = band
        self.dtype = rasterReader.dtypes[0].lower()
        self.crs = targetProjection

        # If there is a polygon, extract the ROI in local referential
        if polygon:
            localProjectionPolygon = projectPolygon(
                polygon, targetProjection, rasterReader.crs)

            self.rasterData, src_transform = mask(
                rasterReader, [localProjectionPolygon], crop=True)

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

            intersectionBounds = localProjectionPolygon.intersection(
                rasterPolygon).bounds
            self.bounds = BoundingBox(*intersectionBounds)
        else:
            self.rasterData = rasterReader.read(1)
            self.width = rasterReader.width
            self.height = rasterReader.height
            self.bounds = rasterReader.bounds
            src_transform = rasterReader.transform

        # Project the raster in the target projection
        self.transform, self.width, self.height = calculate_default_transform(
            rasterReader.crs, targetProjection,
            self.width, self.height, *self.bounds)

        self.bounds = transform_bounds(
            rasterReader.crs, targetProjection, *self.bounds)

        projectedRasterData = np.zeros((self.height, self.width))

        reproject(source=self.rasterData,
                  destination=projectedRasterData,
                  src_crs=rasterReader.crs,
                  src_transform=src_transform,
                  dst_crs=targetProjection,
                  dst_transform=self.transform,
                  resampling=Resampling.nearest)
        self.rasterData = projectedRasterData

        self.metadata = {}

    def createZarrStore(self, zarrRootPath: str,
                        productTimestamp: int,
                        rasterTimestamp: int,
                        chunkMbs=1) -> zarr.DirectoryStore:

        store = zarr.DirectoryStore(path.join(zarrRootPath, self.band))

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

        t = zarr.create(
            shape=(1,),
            dtype="int",
            store=store,
            overwrite=True,
            path="t"
        )
        t[:] = [rasterTimestamp]
        t.attrs['_ARRAY_DIMENSIONS'] = ['t']

        chunkShape = getChunkShape({"x": self.width, "y": self.height, "t": 1},
                                   CStrat.SPINACH)

        # Create zarr array for each band required
        zarray = zarr.create(
            shape=(self.width, self.height, 1),
            chunks=tuple(chunkShape.values()),
            dtype=self.dtype,
            store=store,
            overwrite=True,
            path=self.band
        )

        # Add band metadata to the zarr file
        zarray.attrs['_ARRAY_DIMENSIONS'] = ['x', 'y', 't']

        self.metadata['width'] = self.width
        self.metadata['height'] = self.height
        self.metadata['dtype'] = self.dtype
        self.metadata['bounds'] = self.bounds
        self.metadata['transform'] = self.transform
        self.metadata['crs'] = self.crs
        self.metadata['productTimestamp'] = productTimestamp

        zarray[:, :, 0] = np.flip(np.transpose(self.rasterData), 1)

        # Consolidate the metadata into a single .zmetadata file
        zarr.consolidate_metadata(store)

        return store
