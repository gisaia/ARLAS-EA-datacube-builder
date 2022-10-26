#!/usr/bin/python3

import sys
from pathlib import Path

ROOT_PATH = str(Path(__file__).parent.parent)
sys.path.insert(0, ROOT_PATH)
from models.rasterDrivers.sentinel2_level2A import Sentinel2_Level2A

from utils.objectStore import createInputObjectStore


RASTER_URI = "gs://gisaia-arlasea/S2A_MSIL2A_20221017T105041_N0400_R051_T30TXN_20221017T170159"
BANDS = ["B01"]
TARGET_RESOLUTION = 30

objectStore = createInputObjectStore("gs")
print("Created objectstore")

sentinel2 = Sentinel2_Level2A(objectStore, RASTER_URI,
                              BANDS, TARGET_RESOLUTION)
print(sentinel2.bandsWithResolution)
print(sentinel2.targetResolution)

sentinel2.convert("output/zarr/testSentinel")
