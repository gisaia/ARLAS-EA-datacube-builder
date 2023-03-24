import os.path as path
import re
import zipfile
from datetime import datetime
from typing import Dict

import smart_open as so
from dateutil import parser
from lxml import etree

from models.objectStoreDrivers.abstractObjectStore import AbstractObjectStore
from models.request.rasterProductType import RasterProductType
from models.errors import DownloadError

from .abstractRasterArchive import AbstractRasterArchive

PRODUCT_START_TIME = "metadataSection/metadataObject/metadataWrap/xmlData/" + \
    "safe:acquisitionPeriod/safe:startTime"
PRODUCT_STOP_TIME = "metadataSection/metadataObject/metadataWrap/xmlData/" + \
    "safe:acquisitionPeriod/safe:stopTime"


class Sentinel1_Level1_Safe(AbstractRasterArchive):
    PRODUCT_TYPE = RasterProductType(source="Sentinel1",
                                     format="L1-SAFE")

    def __init__(self, objectStore: AbstractObjectStore, rasterURI: str,
                 bands: Dict[str, str], target_resolution: int,
                 rasterTimestamp: int, zipExtractPath: str):

        self.rasterTimestamp = rasterTimestamp
        self.target_resolution = target_resolution
        self._checkBands(bands)
        self._extract_metadata(objectStore, rasterURI, bands, zipExtractPath)

    def _checkBands(self, bands: Dict[str, str]):
        for band in bands.values():
            if band == "grd-hh":
                continue
            elif band == "grd-hv":
                continue
            elif band == "grd-vh":
                continue
            elif band == "grd-vv":
                continue
            else:
                raise DownloadError(f"Band '{band}' not found")

    def _extract_metadata(self, objectStore: AbstractObjectStore,
                          rasterURI: str, bands: Dict[str, str],
                          zipExtractPath: str):
        self.bandsToExtract = {}

        params = {'client': objectStore.client}

        with so.open(rasterURI, "rb", transport_params=params) as fileBytes:
            with zipfile.ZipFile(fileBytes) as rasterZip:
                listOfFileNames = rasterZip.namelist()
                # Extract timestamp of production of the product
                for fileName in listOfFileNames:
                    if re.match(r".*/manifest\.safe", fileName):
                        if not path.exists(zipExtractPath + fileName):
                            rasterZip.extract(fileName, zipExtractPath)
                        rasterZip.extract(fileName, zipExtractPath)
                        metadata: etree._ElementTree = etree.parse(
                            zipExtractPath + fileName)
                        root: etree._Element = metadata.getroot()
                        startTime = parser.parse(root.xpath(
                            PRODUCT_START_TIME, namespaces=root.nsmap)[0].text)

                        endTime = parser.parse(root.xpath(
                            PRODUCT_STOP_TIME, namespaces=root.nsmap)[0].text)

                        self.productTime = int(
                            (datetime.timestamp(startTime)
                             + datetime.timestamp(endTime)) / 2)
                        break

                for datacubeBand, productBand in bands.items():
                    for fileName in listOfFileNames:
                        if re.match(rf".*/measurement/.*{productBand}.*\.tiff",
                                    fileName):

                            if not path.exists(zipExtractPath + fileName):
                                rasterZip.extract(fileName, zipExtractPath)

                            self.bandsToExtract[datacubeBand] = path.join(
                                zipExtractPath, fileName)

                if len(bands) != len(self.bandsToExtract):
                    raise DownloadError("Some of the required files " +
                                        "were not found")
