import os.path as path
import re
import zipfile
from datetime import datetime
from typing import ClassVar

import smart_open as so
from dateutil import parser
from lxml import etree
from datacube.core.models.enums import SensorFamily

from datacube.core.models.exception import DownloadError
from datacube.core.models.request.rasterProductType import RasterType
from datacube.core.storage.drivers.abstract import AbstractStorage
from datacube.core.rasters.drivers.abstract import AbstractRasterArchive

PRODUCT_TIME = "Product_Characteristics/ACQUISITION_DATE"

# Different resolutions in meters of the Sentinel2 Level2A files
HIGH_RESOLUTION = 10
MED_RESOLUTION = 20


class Sentinel2_Level2A_Theia(AbstractRasterArchive):
    PRODUCT_TYPE: ClassVar[RasterType] = RasterType(source="Sentinel2",
                                                    format="L2A-Theia")
    SENSOR_TYPE: SensorFamily = SensorFamily.RADAR

    def __init__(self, storage: AbstractStorage, raster_uri: str,
                 bands: dict[str, str], target_resolution: int,
                 raster_timestamp: int, zip_extract_path: str):

        self.set_raster_metadata(raster_uri, raster_timestamp)
        self._findBandsResolution(bands, target_resolution)
        self._extract_metadata(storage, raster_uri,
                               bands, zip_extract_path)

    def _findBandsResolution(self, bands: dict[str, str],
                             target_resolution: int):
        # Force the resolution to be higher than HIGH_RESOLUTION
        self.target_resolution = max(HIGH_RESOLUTION, target_resolution)

        self.bandsWithResolution = {}
        for band in bands.values():
            if band == "B1":
                raise DownloadError(title=self.raster_uri,
                                    detail="Band B1 does not exist " +
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
                raise DownloadError(title=self.raster_uri,
                                    detail="Band 'B9' does not exist " +
                                    "in this file format")
            elif band == "B10":
                raise DownloadError(title=self.raster_uri,
                                    detail="Band 'B10' does not exist " +
                                    "in this file format")
            elif band == "B11":
                self.bandsWithResolution[band] = MED_RESOLUTION
            elif band == "B12":
                self.bandsWithResolution[band] = MED_RESOLUTION
            else:
                raise DownloadError(title=self.raster_uri,
                                    detail=f"Band '{band}' not found")

        # target_resolution can not be higher than the resolutions of the bands
        self.target_resolution = min(self.target_resolution,
                                     min(self.bandsWithResolution.values()))

    def _extract_metadata(self, storage: AbstractStorage,
                          raster_uri: str, bands: dict[str, str],
                          zip_extract_path: str):
        self.bands_to_extract = {}

        params = {'client': storage.client}

        with so.open(raster_uri, "rb", transport_params=params) as fb:
            with zipfile.ZipFile(fb) as raster_zip:
                file_names = raster_zip.namelist()
                # Extract timestamp of production of the product
                for f_name in file_names:
                    if re.match(r".*MTD_ALL.xml", f_name):
                        if not path.exists(zip_extract_path + f_name):
                            raster_zip.extract(f_name, zip_extract_path)
                        metadata: etree._ElementTree = etree.parse(
                            zip_extract_path + f_name)
                        root: etree._Element = metadata.getroot()

                        self.product_time = int(datetime.timestamp(
                            parser.parse(root.xpath(
                                PRODUCT_TIME, namespaces=root.nsmap)[0].text)))
                        break

                if not hasattr(self, 'product_time'):
                    raise DownloadError(title=self.raster_uri,
                                        detail="Production time was not found")

                for datacube_band, product_band in bands.items():
                    for f_name in file_names:
                        if re.match(
                                rf".*/.*_FRE_{product_band}\.tif", f_name):
                            if not path.exists(zip_extract_path + f_name):
                                raster_zip.extract(f_name, zip_extract_path)

                            self.bands_to_extract[datacube_band] = path.join(
                                zip_extract_path, f_name)

                if len(bands) != len(self.bands_to_extract):
                    raise DownloadError(title=self.raster_uri,
                                        detail="Some of the required files " +
                                               "were not found")
