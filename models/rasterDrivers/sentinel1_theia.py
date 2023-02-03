import os.path as path
from typing import Dict

import smart_open as so
from urllib.parse import urlparse
import re
from dateutil import parser

from models.objectStoreDrivers.abstractObjectStore import AbstractObjectStore
from models.request.rasterProductType import RasterProductType
from models.errors import DownloadError

from .abstractRasterArchive import AbstractRasterArchive


class Sentinel1_Theia(AbstractRasterArchive):
    PRODUCT_TYPE = RasterProductType(source="Sentinel1",
                                     format="Theia")

    def __init__(self, objectStore: AbstractObjectStore, rasterURI: str,
                 bands: Dict[str, str], targetResolution: int,
                 rasterTimestamp: int, zipExtractPath: str):

        if len(bands) != 1:
            raise DownloadError(
                f"There is only one band in {self.PRODUCT_TYPE.source} " +
                self.PRODUCT_TYPE.format)
        self.rasterTimestamp = rasterTimestamp
        self.targetResolution = targetResolution
        self._extract_metadata(objectStore, rasterURI, bands, zipExtractPath)

    def _extract_metadata(self, objectStore: AbstractObjectStore,
                          rasterURI: str, bands: Dict[str, str],
                          zipExtractPath: str):
        self.bandsToExtract = {}

        params = {'client': objectStore.client}

        with so.open(rasterURI, "rb", transport_params=params) as fileCloud:
            fileName = urlparse(rasterURI).path[1:]

            if len(re.findall(r".*\_(\w*)\.tiff", fileName)) != 1:
                raise DownloadError(f"File {fileName} does not contain " +
                                    "product timestamp in its name.")
            self.productTime = int(parser.parse(
                re.findall(r".*\_(\w*)\.tiff", fileName)[0]).timestamp())

            if not path.exists(zipExtractPath + fileName):
                with open(path.join(zipExtractPath, fileName), "wb") as f:
                    f.write(fileCloud.read())

            self.bandsToExtract[list(bands.keys())[0]] = path.join(
                            zipExtractPath, fileName)

            if len(bands) != len(self.bandsToExtract):
                raise DownloadError("Some of the required files " +
                                    "were not found")
