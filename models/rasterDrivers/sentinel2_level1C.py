import re
from datetime import datetime
from zipfile import ZipFile

from dateutil import parser
from lxml import etree

from .abstractRasterArchive import AbstractRasterArchive

PRODUCT_START_TIME = "n1:General_Info/Product_Info/PRODUCT_START_TIME"
PRODUCT_STOP_TIME = "n1:General_Info/Product_Info/PRODUCT_STOP_TIME"


class Sentinel2_Level1C(AbstractRasterArchive):

    def __init__(self, rasterPath, bands, zipExtractPath="tmp/"):
        self._extract_metadata(rasterPath, bands, zipExtractPath)

    def _extract_metadata(self, rasterPath, bands, zipExtractPath):
        self.bandsToExtract = []

        if rasterPath[-4:] != ".zip":
            raise FileNotFoundError("File does not have the expected format")

        with ZipFile(rasterPath, "r") as zipObj:
            listOfFileNames = zipObj.namelist()
            # Extract timestamp of production of the product
            for fileName in listOfFileNames:
                if re.match(r".*MTD_MSI.*\.xml", fileName):
                    zipObj.extract(fileName, zipExtractPath)
                    metadata: etree._ElementTree = etree.parse(
                        zipExtractPath + fileName)
                    root: etree._Element = metadata.getroot()
                    startTime = parser.parse(root.xpath(
                        PRODUCT_START_TIME, namespaces=root.nsmap)[0].text)

                    endTime = parser.parse(root.xpath(
                        PRODUCT_STOP_TIME, namespaces=root.nsmap)[0].text)

                    self.productTime = int((datetime.timestamp(startTime)
                                            + datetime.timestamp(endTime)) / 2)

            for band in bands:
                for fileName in listOfFileNames:
                    if re.match(r".*/IMG_DATA/.*" + band + r"\.jp2", fileName):
                        zipObj.extract(fileName, zipExtractPath)
                        self.bandsToExtract.append(zipExtractPath + fileName)
