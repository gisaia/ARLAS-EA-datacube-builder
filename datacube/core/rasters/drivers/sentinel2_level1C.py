import re
from datetime import datetime
from zipfile import ZipFile

from dateutil import parser
from lxml import etree

from datacube.core.rasters.drivers.abstract import AbstractRasterArchive

PRODUCT_START_TIME = "n1:General_Info/Product_Info/PRODUCT_START_TIME"
PRODUCT_STOP_TIME = "n1:General_Info/Product_Info/PRODUCT_STOP_TIME"


@DeprecationWarning
class Sentinel2_Level1C(AbstractRasterArchive):

    def __init__(self, raster_path, bands, zip_extract_path="tmp/"):
        self._extract_metadata(raster_path, bands, zip_extract_path)

    def _extract_metadata(self, raster_path, bands, zip_extract_path):
        self.bands_to_extract = []

        if raster_path[-4:] != ".zip":
            raise FileNotFoundError("File does not have the expected format")

        with ZipFile(raster_path, "r") as zipObj:
            file_names = zipObj.namelist()
            # Extract timestamp of production of the product
            for f_name in file_names:
                if re.match(r".*MTD_MSI.*\.xml", f_name):
                    zipObj.extract(f_name, zip_extract_path)
                    metadata: etree._ElementTree = etree.parse(
                        zip_extract_path + f_name)
                    root: etree._Element = metadata.getroot()
                    start_time = parser.parse(root.xpath(
                        PRODUCT_START_TIME, namespaces=root.nsmap)[0].text)

                    end_time = parser.parse(root.xpath(
                        PRODUCT_STOP_TIME, namespaces=root.nsmap)[0].text)

                    self.product_time = int(
                        (datetime.timestamp(start_time)
                         + datetime.timestamp(end_time)) / 2)
                    break

            for band in bands:
                for f_name in file_names:
                    if re.match(r".*/IMG_DATA/.*" + band + r"\.jp2", f_name):
                        zipObj.extract(f_name, zip_extract_path)
                        self.bands_to_extract.append(
                            zip_extract_path + f_name)
