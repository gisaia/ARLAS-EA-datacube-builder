import hazelcast
from hazelcast.config import Config

from datacube.core.rasters.drivers.abstract import (
    AbstractRasterArchive, CachedAbstractRasterArchive)

CONFIG = Config()


class CacheManager:
    __MAP_NAME = "rasters"

    def __init__(self):
        self.__client = hazelcast.HazelcastClient(CONFIG)
        self.__map = self.__client.get_map(
            CacheManager.__MAP_NAME).blocking()

    def put_raster(self, raster: AbstractRasterArchive) \
            -> CachedAbstractRasterArchive | None:
        self.__map.put(raster.raster_uri, raster.cache_information())

    def get(self, key: str) \
            -> CachedAbstractRasterArchive | None:
        return self.__map.get(key)

    def shutdown(self):
        self.__client.shutdown()
