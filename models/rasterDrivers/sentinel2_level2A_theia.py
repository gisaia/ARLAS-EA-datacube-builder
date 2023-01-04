import re
import zipfile
from datetime import datetime

import smart_open as so
from dateutil import parser
from lxml import etree

from models.objectStoreDrivers.abstractObjectStore import AbstractObjectStore

from .abstractRasterArchive import AbstractRasterArchive

PRODUCT_TIME = "Product_Characteristics/ACQUISITION_DATE"

# Different resolutions in meters of the Sentinel2 Level2A files
HIGH_RESOLUTION = 10
MED_RESOLUTION = 20


class Sentinel2_Level2A_Theia(AbstractRasterArchive):

    def __init__(self, objectStore: AbstractObjectStore, rasterURI, bands,
                 targetResolution, rasterTimestamp, zipExtractPath="tmp/"):

        self.rasterTimestamp = rasterTimestamp
        self._findBandsResolution(bands, targetResolution)
        self._extract_metadata(objectStore, rasterURI, bands, zipExtractPath)

    def _findBandsResolution(self, bands, targetResolution):
        # Force the resolution to be higher than HIGH_RESOLUTION
        self.targetResolution = max(HIGH_RESOLUTION, targetResolution)

        self.bandsWithResolution = {}
        for band in bands:
            if band == "B1":
                raise FileNotFoundError("Band B1 does not exist \
                                        in this file format")
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
                raise FileNotFoundError("Band 'B9' does not exist \
                                        in this file format")
            elif band == "B10":
                raise FileNotFoundError("Band 'B10' does not exist \
                                        in this file format")
            elif band == "B11":
                self.bandsWithResolution[band] = MED_RESOLUTION
            elif band == "B12":
                self.bandsWithResolution[band] = MED_RESOLUTION
            else:
                raise FileNotFoundError(f"Band '{band}' not found")

        # targetResolution can not be higher than the resolutions of the bands
        self.targetResolution = min(self.targetResolution,
                                    min(self.bandsWithResolution.values()))

    def _extract_metadata(self, objectStore, rasterURI, bands, zipExtractPath):
        self.bandsToExtract = {}

        params = {'client': objectStore.client}

        with so.open(rasterURI, "rb", transport_params=params) as fileBytes:
            with zipfile.ZipFile(fileBytes) as rasterZip:
                listOfFileNames = rasterZip.namelist()
                # Extract timestamp of production of the product
                for fileName in listOfFileNames:
                    if re.match(r".*MTD_ALL.xml", fileName):
                        rasterZip.extract(fileName, zipExtractPath)
                        metadata: etree._ElementTree = etree.parse(
                            zipExtractPath + fileName)
                        root: etree._Element = metadata.getroot()

                        self.productTime = int(datetime.timestamp(
                            parser.parse(root.xpath(
                                PRODUCT_TIME, namespaces=root.nsmap)[0].text)))
                        break

                for band in bands:
                    for fileName in listOfFileNames:
                        if re.match(rf".*/.*_FRE_{band}\.tif", fileName):

                            rasterZip.extract(fileName, zipExtractPath)
                            self.bandsToExtract[band] = zipExtractPath + \
                                fileName

                if len(bands) != len(self.bandsToExtract):
                    raise FileNotFoundError("Some of the required files" +
                                            "were not found")
