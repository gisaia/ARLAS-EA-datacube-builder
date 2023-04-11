import os.path as path
import re
import zipfile
from datetime import datetime

import smart_open as so
from dateutil import parser
from lxml import etree

from datacube.core.object_store.drivers.abstract import AbstractObjectStore
from datacube.core.models.request.rasterProductType import RasterType
from datacube.core.models.errors import DownloadError
from datacube.core.rasters.drivers.abstract import AbstractRasterArchive

PRODUCT_TIME = "Product_Characteristics/" + \
    "UTC_Acquisition_Range/MEAN"

RESOLUTION = 20  # m


class TheiaSnow(AbstractRasterArchive):
    PRODUCT_TYPE = RasterType(source="Theia",
                              format="Snow")

    def __init__(self, object_store: AbstractObjectStore, raster_uri: str,
                 bands: dict[str, str], target_resolution: int,
                 raster_timestamp: int, zip_extract_path: str):

        self.raster_timestamp = raster_timestamp
        self.target_resolution = target_resolution
        self.__check_bands(bands)
        self._extract_metadata(object_store, raster_uri,
                               bands, zip_extract_path)

    def __check_bands(self, bands: dict[str, str]):
        for band in bands.values():
            if band == "SCD":
                continue
            elif band == "SMD":
                continue
            elif band == "SOD":
                continue
            else:
                raise DownloadError(f"Band '{band}' not found")

    def _extract_metadata(self, object_store: AbstractObjectStore,
                          raster_uri: str, bands: dict[str, str],
                          zip_extract_path: str):
        self.bands_to_extract = {}

        params = {'client': object_store.client}

        with so.open(raster_uri, "rb", transport_params=params) as fb:
            with zipfile.ZipFile(fb) as raster_zip:
                file_names = raster_zip.namelist()
                # Extract timestamp of production of the product
                for f_name in file_names:
                    if re.match(r".*/.*\_ALL\.xml", f_name):
                        if not path.exists(zip_extract_path + f_name):
                            raster_zip.extract(f_name, zip_extract_path)
                        raster_zip.extract(f_name, zip_extract_path)
                        metadata: etree._ElementTree = etree.parse(
                            zip_extract_path + f_name)
                        root: etree._Element = metadata.getroot()

                        self.product_time = int(datetime.timestamp(
                            parser.parse(root.xpath(
                                PRODUCT_TIME,
                                namespaces=root.nsmap)[0].text)))
                        break

                for datacube_band, product_band in bands.items():
                    for f_name in file_names:
                        if re.match(rf".*/.*{product_band}_R2.tif", f_name):
                            if not path.exists(zip_extract_path + f_name):
                                raster_zip.extract(f_name, zip_extract_path)

                            self.bands_to_extract[datacube_band] = path.join(
                                zip_extract_path, f_name)

                if len(bands) != len(self.bands_to_extract):
                    raise DownloadError("Some of the required bands " +
                                        "were not found")
