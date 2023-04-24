from typing import Any

import hazelcast
from hazelcast.config import Config
from hazelcast.future import Future

from datacube.core.rasters.drivers.abstract import AbstractRasterArchive

CONFIG = Config()


class CacheManager:
    __MAP_NAME = "rasters"

    def __init__(self, blocking=True):
        self.__client = hazelcast.HazelcastClient(CONFIG)
        if blocking:
            self.__map = self.__client.get_map(
                CacheManager.__MAP_NAME).blocking()
        else:
            self.__map = self.__client.get_map(
                CacheManager.__MAP_NAME)

    def put_raster(self, raster: AbstractRasterArchive) \
            -> Future[Any | None] | Any | None:
        self.__map.put(raster.raster_uri, raster.cache_information())

    def get(self, key: str) \
            -> Future[dict[str, Any] | None] | dict[str, Any] | None:
        return self.__map.get(key)

    def shutdown(self):
        self.__client.shutdown()
