#!/usr/bin/python3

import os
import re
import sys
from zipfile import ZipFile

from shapely.geometry import Polygon

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__))[:-6])
from utils.raster2zarr import convert

# RASTER_FILE = "./data/soilClassificationwithMachineLearningwithPythonScikitLearn/S2B_MSIL1C_20200917T151709_N0209_R125_T18LUM_20200917T203629.SAFE/GRANULE/L1C_T18LUM_A018455_20200917T151745/IMG_DATA/T18LUM_20200917T151709_B01.jp2"
RASTER_ZIP_FILE = "./data/soilClassificationwithMachineLearningwithPythonScikitLearn.zip"
ZARR_FILE = "./output/zarr/testFullFile"
BANDS = ["B01", "B02", "B03", "B04"]

bandsToExtract = []
with ZipFile(RASTER_ZIP_FILE, "r") as zipObj:
    listOfFileNames = zipObj.namelist()
    for band in BANDS:
        for fileName in listOfFileNames:
            if re.match(".*/IMG_DATA/.*" + band + "\.jp2", fileName):
                zipObj.extract(fileName, "tmp")
                bandsToExtract.append("tmp/" + fileName)

polygon = Polygon([(383700.0, 8651200.0), (397400.0, 8651200.0),
                   (397400.0, 8642300.0), (383700.0, 8642300.0),
                   (383700.0, 8651200.0)])

convert(bandsToExtract, ZARR_FILE, None)
