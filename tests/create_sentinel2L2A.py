#!/usr/bin/python3

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__))[:-6])
from utils.drivers.sentinel2_level2A import Sentinel2_Level2A


RASTER_ZIP_PATH = "./data/S2A_MSIL2A_20220809T102041_N0400_R065_T32TML_20220809T180703.zip"
BANDS = ["B01", "B12"]
TARGET_RESOLUTION = 30

sentinel2 = Sentinel2_Level2A(RASTER_ZIP_PATH, BANDS, TARGET_RESOLUTION)
print(sentinel2.bandsWithResolution)
print(sentinel2.targetResolution)

sentinel2._extract_metadata()
