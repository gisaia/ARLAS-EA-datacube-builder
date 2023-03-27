import os.path as path
from typing import Dict

import smart_open as so
from urllib.parse import urlparse
import re
from dateutil import parser

from datacube.core.object_store.drivers.abstract import AbstractObjectStore
from datacube.core.models.request.rasterProductType import RasterProductType
from datacube.core.models.errors import DownloadError
from datacube.core.rasters.drivers.abstract import AbstractRasterArchive


class Sentinel1_Theia(AbstractRasterArchive):
    PRODUCT_TYPE = RasterProductType(source="Sentinel1",
                                     format="Theia")

    def __init__(self, object_store: AbstractObjectStore, raster_uri: str,
                 bands: Dict[str, str], target_resolution: int,
                 raster_timestamp: int, zip_extract_path: str):

        if len(bands) != 1:
            raise DownloadError(
                f"There is only one band in {self.PRODUCT_TYPE.source} " +
                self.PRODUCT_TYPE.format)
        self.raster_timestamp = raster_timestamp
        self.target_resolution = target_resolution
        self._extract_metadata(object_store, raster_uri,
                               bands, zip_extract_path)

    def _extract_metadata(self, object_store: AbstractObjectStore,
                          raster_uri: str, bands: Dict[str, str],
                          zip_extract_path: str):
        self.bands_to_extract = {}

        params = {'client': object_store.client}

        with so.open(raster_uri, "rb", transport_params=params) as fileCloud:
            f_name = urlparse(raster_uri).path[1:]

            if len(re.findall(r".*\_(\w*)\.tiff", f_name)) != 1:
                raise DownloadError(f"File {f_name} does not contain " +
                                    "product timestamp in its name.")
            self.product_time = int(parser.parse(
                re.findall(r".*\_(\w*)\.tiff", f_name)[0]).timestamp())

            if not path.exists(zip_extract_path + f_name):
                with open(path.join(zip_extract_path, f_name), "wb") as f:
                    f.write(fileCloud.read())

            self.bands_to_extract[list(bands.keys())[0]] = path.join(
                            zip_extract_path, f_name)

            if len(bands) != len(self.bands_to_extract):
                raise DownloadError("Some of the required files " +
                                    "were not found")
