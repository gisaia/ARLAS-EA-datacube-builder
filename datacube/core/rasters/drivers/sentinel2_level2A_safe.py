import os.path as path
import re
import zipfile
from datetime import datetime
from typing import ClassVar

import smart_open as so
from dateutil import parser
from lxml import etree

from datacube.core.models.errors import DownloadError
from datacube.core.models.request.rasterProductType import RasterType
from datacube.core.object_store.drivers.abstract import AbstractObjectStore
from datacube.core.rasters.drivers.abstract import AbstractRasterArchive

PRODUCT_START_TIME = "n1:General_Info/Product_Info/PRODUCT_START_TIME"
PRODUCT_STOP_TIME = "n1:General_Info/Product_Info/PRODUCT_STOP_TIME"

# Different resolutions in meters of the Sentinel2 Level2A files
HIGH_RESOLUTION = 10
MED_RESOLUTION = 20
LOW_RESOLUTION = 60


class Sentinel2_Level2A_Safe(AbstractRasterArchive):
    PRODUCT_TYPE: ClassVar[RasterType] = RasterType(source="Sentinel2",
                                                    format="L2A-SAFE")

    def __init__(self, object_store: AbstractObjectStore, raster_uri: str,
                 bands: dict[str, str], target_resolution: int,
                 raster_timestamp: int, zip_extract_path: str):

        self.set_raster_metadata(raster_uri, raster_timestamp)
        self._findBandsResolution(bands, target_resolution)
        self._extract_metadata(object_store, raster_uri,
                               bands, zip_extract_path)

    def _findBandsResolution(self, bands: dict[str, str],
                             target_resolution: int):
        # Force the resolution to be higher than HIGH_RESOLUTION
        self.target_resolution = max(HIGH_RESOLUTION, target_resolution)
        # Force the resolution to be at least of the most precise band
        if "B08" in bands:
            self.target_resolution = HIGH_RESOLUTION

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

        # target_resolution can not be higher than the resolutions of the bands
        self.target_resolution = min(self.target_resolution,
                                     min(self.bandsWithResolution.values()))

    def _bandAvailableEveryResolution(self, band):
        if HIGH_RESOLUTION <= self.target_resolution < MED_RESOLUTION:
            self.bandsWithResolution[band] = HIGH_RESOLUTION
        elif self.target_resolution < LOW_RESOLUTION:
            self.bandsWithResolution[band] = MED_RESOLUTION
        else:
            self.bandsWithResolution[band] = LOW_RESOLUTION

    def _bandAvailableMedAndLowResolution(self, band):
        if self.target_resolution < LOW_RESOLUTION:
            self.bandsWithResolution[band] = MED_RESOLUTION
        else:
            self.bandsWithResolution[band] = LOW_RESOLUTION

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
                    if re.match(r".*MTD_MSI.*\.xml", f_name):
                        if not path.exists(zip_extract_path + f_name):
                            raster_zip.extract(f_name, zip_extract_path)
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

                if not hasattr(self, 'product_time'):
                    raise DownloadError(
                        f"{self.raster_uri}'s production time was not found")

                for datacube_band, product_band in bands.items():
                    bandResolution = self.bandsWithResolution[product_band]
                    for f_name in file_names:
                        if re.match(rf".*/IMG_DATA/R{bandResolution}m/.*" +
                                    rf"{product_band}_{bandResolution}m\.jp2",
                                    f_name):

                            if not path.exists(zip_extract_path + f_name):
                                raster_zip.extract(f_name, zip_extract_path)

                            self.bands_to_extract[datacube_band] = path.join(
                                zip_extract_path, f_name)

                if len(bands) != len(self.bands_to_extract):
                    raise DownloadError("Some of the required files " +
                                        "were not found")
