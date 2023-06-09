import json
import os.path as path
import re
import tarfile
from datetime import datetime
from typing import ClassVar

import smart_open as so

from datacube.core.models.exception import DownloadError
from datacube.core.models.request.rasterProductType import RasterType
from datacube.core.storage.drivers.abstract import AbstractStorage
from datacube.core.rasters.drivers.abstract import AbstractRasterArchive

PRODUCT_TIME = "Product_Characteristics/ACQUISITION_DATE"

# Different resolutions in meters of the Sentinel2 Level1C files
HIGH_RESOLUTION = 10


class Sentinel2_Level1C_Pivot(AbstractRasterArchive):
    PRODUCT_TYPE: ClassVar[RasterType] = RasterType(source="Sentinel2",
                                                    format="L1C-Pivot")

    def __init__(self, storage: AbstractStorage, raster_uri: str,
                 bands: dict[str, str], target_resolution: int,
                 raster_timestamp: int, zip_extract_path: str):

        self.set_raster_metadata(raster_uri, raster_timestamp)
        self.target_resolution = target_resolution
        self.__check_bands(bands)
        self._extract_metadata(storage, raster_uri,
                               bands, zip_extract_path)

    def __check_bands(self, bands: dict[str, str]):
        for band in bands.values():
            if re.match(r"B0[0-9]", band):
                continue
            elif band == "B8A":
                continue
            elif band == "B10":
                continue
            elif band == "B11":
                continue
            elif band == "B12":
                continue
            elif band == "TCI":
                continue
            else:
                raise DownloadError(title=self.raster_uri,
                                    detail=f"Band '{band}' not found")

    def _extract_metadata(self, storage: AbstractStorage,
                          raster_uri: str, bands: dict[str, str],
                          zip_extract_path: str):
        self.bands_to_extract = {}

        params = {'client': storage.client}

        with so.open(raster_uri, "rb", transport_params=params) as fb:
            with tarfile.open(fileobj=fb) as raster_tar:
                file_names = raster_tar.getnames()
                # Extract timestamp of production of the product
                for f_name in file_names:
                    if re.match(r".*/CAT_S2A_MSI__L1C_.*.JSON", f_name):
                        if not path.exists(zip_extract_path + f_name):
                            raster_tar.extract(f_name, zip_extract_path)
                        with open(zip_extract_path + f_name, 'r') as f:
                            product_datetime: str = json.load(
                                f)["properties"]["datetime"]
                            self.product_time = datetime.timestamp(
                                datetime.fromisoformat(
                                    product_datetime.replace('Z', '+00:00')))
                        break

                if not hasattr(self, 'product_time'):
                    raise DownloadError(title=self.raster_uri,
                                        detail="Production time was not found")

                for datacube_band, product_band in bands.items():
                    for f_name in file_names:
                        if re.match(rf".*/IMG_MSI_{product_band}_10m" +
                                    r"_S2A_MSI__L1C_.*\.JP2", f_name):
                            if not path.exists(zip_extract_path + f_name):
                                raster_tar.extract(f_name, zip_extract_path)

                            self.bands_to_extract[datacube_band] = path.join(
                                zip_extract_path, f_name)

                if len(bands) != len(self.bands_to_extract):
                    raise DownloadError(title=self.raster_uri,
                                        detail="Some of the required files " +
                                               "were not found")
