import os.path as path
import re
from typing import ClassVar
from urllib.parse import urlparse

import smart_open as so
from dateutil import parser

from datacube.core.models.exception import DownloadError
from datacube.core.models.request.rasterProductType import RasterType
from datacube.core.object_store.drivers.abstract import AbstractObjectStore
from datacube.core.rasters.drivers.abstract import AbstractRasterArchive


class Sentinel1_Theia(AbstractRasterArchive):
    PRODUCT_TYPE: ClassVar[RasterType] = RasterType(source="Sentinel1",
                                                    format="Theia")

    def __init__(self, object_store: AbstractObjectStore, raster_uri: str,
                 bands: dict[str, str], target_resolution: int,
                 raster_timestamp: int, zip_extract_path: str):

        if len(bands) != 1:
            raise DownloadError(title=self.raster_uri,
                                detail="There is only one band in products " +
                                       f"of type {self.PRODUCT_TYPE.to_key()}")
        self.set_raster_metadata(raster_uri, raster_timestamp)
        self.target_resolution = target_resolution
        self._extract_metadata(object_store, raster_uri,
                               bands, zip_extract_path)

    def _extract_metadata(self, object_store: AbstractObjectStore,
                          raster_uri: str, bands: dict[str, str],
                          zip_extract_path: str):
        self.bands_to_extract = {}

        params = {'client': object_store.client}

        with so.open(raster_uri, "rb", transport_params=params) as fileCloud:
            f_name = urlparse(raster_uri).path[1:]

            if len(re.findall(r".*\_(\w*)\.tiff", f_name)) != 1:
                raise DownloadError(title=self.raster_uri,
                                    detail=f"File {f_name} does not contain " +
                                    "product timestamp in its name.")
            self.product_time = int(parser.parse(
                re.findall(r".*\_(\w*)\.tiff", f_name)[0]).timestamp())

            if not hasattr(self, 'product_time'):
                raise DownloadError(title=self.raster_uri,
                                    detail="Production time was not found")

            if not path.exists(zip_extract_path + f_name):
                with open(path.join(zip_extract_path, f_name), "wb") as f:
                    f.write(fileCloud.read())

            self.bands_to_extract[list(bands.keys())[0]] = path.join(
                            zip_extract_path, f_name)

            if len(bands) != len(self.bands_to_extract):
                raise DownloadError(title=self.raster_uri,
                                    detail="Some of the required files " +
                                           "were not found")
