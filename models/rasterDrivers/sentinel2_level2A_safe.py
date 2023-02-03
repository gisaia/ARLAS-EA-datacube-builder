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

PRODUCT_START_TIME = "n1:General_Info/Product_Info/PRODUCT_START_TIME"
PRODUCT_STOP_TIME = "n1:General_Info/Product_Info/PRODUCT_STOP_TIME"

# Different resolutions in meters of the Sentinel2 Level2A files
HIGH_RESOLUTION = 10
MED_RESOLUTION = 20
LOW_RESOLUTION = 60


class Sentinel2_Level2A_Safe(AbstractRasterArchive):
    PRODUCT_TYPE = RasterProductType(source="Sentinel2",
                                     format="L2A-SAFE")

    def __init__(self, objectStore: AbstractObjectStore, rasterURI: str,
                 bands: Dict[str, str], targetResolution: int,
                 rasterTimestamp: int, zipExtractPath: str):

        self.rasterTimestamp = rasterTimestamp
        self._findBandsResolution(bands, targetResolution)
        self._extract_metadata(objectStore, rasterURI, bands, zipExtractPath)

    def _findBandsResolution(self, bands: Dict[str, str],
                             targetResolution: int):
        # Force the resolution to be higher than HIGH_RESOLUTION
        self.targetResolution = max(HIGH_RESOLUTION, targetResolution)
        # Force the resolution to be at least of the most precise band
        if "B08" in bands:
            self.targetResolution = HIGH_RESOLUTION

        self.bandsWithResolution = {}
        for band in bands.values():
            if band == "AOT":
                self._bandAvailableEveryResolution(band)
            elif band == "B01":
                self._bandAvailableMedAndLowResolution(band)
            elif band == "B02":
                self._bandAvailableEveryResolution(band)
            elif band == "B03":
                self._bandAvailableEveryResolution(band)
            elif band == "B04":
                self._bandAvailableEveryResolution(band)
            elif band == "B05":
                self._bandAvailableMedAndLowResolution(band)
            elif band == "B06":
                self._bandAvailableMedAndLowResolution(band)
            elif band == "B07":
                self._bandAvailableMedAndLowResolution(band)
            elif band == "B08":
                self.bandsWithResolution[band] = HIGH_RESOLUTION
            elif band == "B8A":
                self._bandAvailableMedAndLowResolution(band)
            elif band == "B09":
                self.bandsWithResolution[band] = LOW_RESOLUTION
            elif band == "B10":
                raise DownloadError("Band 'B10' does not exist" +
                                    "in Sentinel2-L2A files")
            elif band == "B11":
                self._bandAvailableMedAndLowResolution(band)
            elif band == "B12":
                self._bandAvailableMedAndLowResolution(band)
            elif band == "SCL":
                self._bandAvailableMedAndLowResolution(band)
            elif band == "TCI":
                self._bandAvailableEveryResolution(band)
            elif band == "WVP":
                self._bandAvailableEveryResolution(band)
            else:
                raise DownloadError(f"Band '{band}' not found")

        # targetResolution can not be higher than the resolutions of the bands
        self.targetResolution = min(self.targetResolution,
                                    min(self.bandsWithResolution.values()))

    def _bandAvailableEveryResolution(self, band):
        if HIGH_RESOLUTION <= self.targetResolution < MED_RESOLUTION:
            self.bandsWithResolution[band] = HIGH_RESOLUTION
        elif self.targetResolution < LOW_RESOLUTION:
            self.bandsWithResolution[band] = MED_RESOLUTION
        else:
            self.bandsWithResolution[band] = LOW_RESOLUTION

    def _bandAvailableMedAndLowResolution(self, band):
        if self.targetResolution < LOW_RESOLUTION:
            self.bandsWithResolution[band] = MED_RESOLUTION
        else:
            self.bandsWithResolution[band] = LOW_RESOLUTION

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
                    if re.match(r".*MTD_MSI.*\.xml", fileName):
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
                    bandResolution = self.bandsWithResolution[productBand]
                    for fileName in listOfFileNames:
                        if re.match(rf".*/IMG_DATA/R{bandResolution}m/" +
                                    rf".*{productBand}_{bandResolution}m\.jp2",
                                    fileName):

                            if not path.exists(zipExtractPath + fileName):
                                rasterZip.extract(fileName, zipExtractPath)

                            self.bandsToExtract[datacubeBand] = path.join(
                                zipExtractPath, fileName)

                if len(bands) != len(self.bandsToExtract):
                    raise DownloadError("Some of the required files " +
                                        "were not found")
