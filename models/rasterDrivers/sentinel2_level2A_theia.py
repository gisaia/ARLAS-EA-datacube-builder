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

PRODUCT_TIME = "Product_Characteristics/ACQUISITION_DATE"

# Different resolutions in meters of the Sentinel2 Level2A files
HIGH_RESOLUTION = 10
MED_RESOLUTION = 20


class Sentinel2_Level2A_Theia(AbstractRasterArchive):
    PRODUCT_TYPE = RasterProductType(source="Sentinel2",
                                     format="2A-Theia")

    def __init__(self, objectStore: AbstractObjectStore, rasterURI: str,
                 bands: Dict[str, str], targetResolution: int,
                 rasterTimestamp: int, zipExtractPath: int):

        self.rasterTimestamp = rasterTimestamp
        self._findBandsResolution(bands, targetResolution)
        self._extract_metadata(objectStore, rasterURI, bands, zipExtractPath)

    def _findBandsResolution(self, bands: Dict[str, str],
                             targetResolution: int):
        # Force the resolution to be higher than HIGH_RESOLUTION
        self.targetResolution = max(HIGH_RESOLUTION, targetResolution)

        self.bandsWithResolution = {}
        for band in bands.values():
            if band == "B1":
                raise DownloadError("Band B1 does not exist " +
                                    "in this file format")
            elif band == "B2":
                self.bandsWithResolution[band] = HIGH_RESOLUTION
            elif band == "B3":
                self.bandsWithResolution[band] = HIGH_RESOLUTION
            elif band == "B4":
                self.bandsWithResolution[band] = HIGH_RESOLUTION
            elif band == "B5":
                self.bandsWithResolution[band] = MED_RESOLUTION
            elif band == "B6":
                self.bandsWithResolution[band] = MED_RESOLUTION
            elif band == "B7":
                self.bandsWithResolution[band] = MED_RESOLUTION
            elif band == "B8":
                self.bandsWithResolution[band] = HIGH_RESOLUTION
            elif band == "B8A":
                self.bandsWithResolution[band] = MED_RESOLUTION
            elif band == "B9":
                raise DownloadError("Band 'B9' does not exist " +
                                    "in this file format")
            elif band == "B10":
                raise DownloadError("Band 'B10' does not exist " +
                                    "in this file format")
            elif band == "B11":
                self.bandsWithResolution[band] = MED_RESOLUTION
            elif band == "B12":
                self.bandsWithResolution[band] = MED_RESOLUTION
            else:
                raise DownloadError(f"Band '{band}' not found")

        # targetResolution can not be higher than the resolutions of the bands
        self.targetResolution = min(self.targetResolution,
                                    min(self.bandsWithResolution.values()))

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
                    if re.match(r".*MTD_ALL.xml", fileName):
                        if not path.exists(zipExtractPath + fileName):
                            rasterZip.extract(fileName, zipExtractPath)
                        rasterZip.extract(fileName, zipExtractPath)
                        metadata: etree._ElementTree = etree.parse(
                            zipExtractPath + fileName)
                        root: etree._Element = metadata.getroot()

                        self.productTime = int(datetime.timestamp(
                            parser.parse(root.xpath(
                                PRODUCT_TIME, namespaces=root.nsmap)[0].text)))
                        break

                for datacubeBand, productBand in bands.items():
                    for fileName in listOfFileNames:
                        if re.match(
                                rf".*/.*_FRE_{productBand}\.tif", fileName):
                            if not path.exists(zipExtractPath + fileName):
                                rasterZip.extract(fileName, zipExtractPath)

                            self.bandsToExtract[datacubeBand] = path.join(
                                zipExtractPath, fileName)

                if len(bands) != len(self.bandsToExtract):
                    raise DownloadError("Some of the required files" +
                                        "were not found")
