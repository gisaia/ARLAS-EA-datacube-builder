import hashlib
import json
import os
import os.path as path

from datacube.core.rasters.drivers.abstract import (
    AbstractRasterArchive, CachedAbstractRasterArchive)

CACHE_DIR = "cache"


def _uri2cache_path(uri: str) -> str:
    return path.join(CACHE_DIR,
                     hashlib.sha256(uri.encode()).hexdigest())


class CacheManager:
    @classmethod
    def put_raster(cls, raster: AbstractRasterArchive):
        """
        Stores a raster archive's metadata in a json file,
        named after the hash of the archive's location.
        """
        with open(_uri2cache_path(raster.raster_uri), 'w') as f:
            json.dump(raster.cache_information().dict(), f)

    @classmethod
    def get(cls, key) -> CachedAbstractRasterArchive:
        """
        Retrieve a cached raster archive's metadata to be used for the cube's
        metadata construction. Also removes the metadata from the cache.
        """
        with open(_uri2cache_path(key), 'r') as f:
            raster = CachedAbstractRasterArchive(**json.load(f))
        os.remove(_uri2cache_path(key))
        return raster
