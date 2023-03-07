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

PRODUCT_TIME = "Product_Characteristics/" + \
    "UTC_Acquisition_Range/MEAN"

RESOLUTION = 20  # m


class TheiaSnow(AbstractRasterArchive):
    PRODUCT_TYPE = RasterProductType(source="Theia",
                                     format="Snow")

    def __init__(self, objectStore: AbstractObjectStore, rasterURI: str,
                 bands: Dict[str, str], targetResolution: int,
                 rasterTimestamp: int, zipExtractPath: str):

        self.rasterTimestamp = rasterTimestamp
        self.targetResolution = targetResolution
        self._checkBands(bands)
        self._extract_metadata(objectStore, rasterURI, bands, zipExtractPath)

    def _checkBands(self, bands: Dict[str, str]):
        for band in bands.values():
            if band == "SCD":
                continue
            elif band == "SMD":
                continue
            elif band == "SOD":
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
                    if re.match(r".*/.*\_ALL\.xml", fileName):
                        if not path.exists(zipExtractPath + fileName):
                            rasterZip.extract(fileName, zipExtractPath)
                        rasterZip.extract(fileName, zipExtractPath)
                        metadata: etree._ElementTree = etree.parse(
                            zipExtractPath + fileName)
                        root: etree._Element = metadata.getroot()

                        self.productTime = int(datetime.timestamp(parser.parse(
                            root.xpath(PRODUCT_TIME,
                                       namespaces=root.nsmap)[0].text)))
                        break

                for datacubeBand, productBand in bands.items():
                    for fileName in listOfFileNames:
                        if re.match(rf".*/.*{productBand}_R2.tif", fileName):
                            if not path.exists(zipExtractPath + fileName):
                                rasterZip.extract(fileName, zipExtractPath)

                            self.bandsToExtract[datacubeBand] = path.join(
                                zipExtractPath, fileName)

                if len(bands) != len(self.bandsToExtract):
                    raise DownloadError("Some of the required bands " +
                                        "were not found")
