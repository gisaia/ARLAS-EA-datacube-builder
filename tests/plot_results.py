#!/usr/bin/python3

import os
import sys

import matplotlib.pyplot as plt
import rasterio
import xarray as xr

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__))[:-6])

from app import App
from models.drivers.sentinel2_level2A import Sentinel2_Level2A

#####################################
#############   PARAMS   ############
#####################################

FILE_1 = "./data/S2A_MSIL2A_20220809T102041_N0400_R065_T32TML_20220809T180703"
FILE_1_IMG_ROOT_NAME = "sardaigne_1"
FILE_2 = "./data/S2B_MSIL2A_20220814T101559_N0400_R065_T32TML_20220814T130923"
FILE_2_IMG_ROOT_NAME = "sardaigne_2"

ZARRFILE = "./output/zarr/post"
ROI = "400000.0,4480000.0,500000.0,4600000.0"
BANDS = ["B01"]
TARGET_RESOLUTION = 20

OUTPUT_IMG_ROOT_NAME = "sardaigne"

OUTPUT_DIR = "./output/images/"

#####################################
############   METHODS   ############
#####################################


def plotInputBands(zipFile, bands, targetResolution,
                   imgRootName, cmap="Blues"):

    sentinel2Raster = Sentinel2_Level2A(zipFile, bands, targetResolution)
    for band in bands:
        print(f"Printing {band} for {zipFile}")
        rasterBand = rasterio.open(sentinel2Raster.bandsToExtract[band])

        ax = plt.subplot()
        img = ax.imshow(rasterBand.read(1), cmap=cmap)
        plt.colorbar(img)
        plt.savefig(f"{OUTPUT_DIR}input/{imgRootName}_{band}")


def plotOutputBands(zarrFile, bands, imgRootName, cmap="Blues"):
    ds = xr.open_zarr(zarrFile)
    for time in ds.t:
        for band in bands:
            print(f"Printing {band} for {zarrFile} at time {int(time)}")
            ax = plt.subplot()
            ds.get(band).sel(t=time).plot(x="x", y="y", cmap=cmap, ax=ax)
            plt.savefig(f"{OUTPUT_DIR}output/{imgRootName}_{band}_{int(time)}")


#####################################
###########   LAUNCH APP   ##########
#####################################

# Start app
app = App()

# Post request to convert a ZARR
app.app.post("/raster2zarr/convert", data=dict(
    rasterFile=[{
        "rasterFormat": "Sentinel2-2A",
        "rasterPath": f"{FILE_1}.zip"
    }, {
        "rasterFormat": "Sentinel2-2A",
        "rasterPath":  f"{FILE_2}.zip",
    }],
    zarrFile=ZARRFILE,
    roi=ROI,
    bands=BANDS,
    targetResolution=TARGET_RESOLUTION
))

#####################################
##############   PLOT   #############
#####################################
print("---- Plotting inputs ----")
plotInputBands(f"{FILE_1}.zip", BANDS,
               TARGET_RESOLUTION, FILE_1_IMG_ROOT_NAME)
plotInputBands(f"{FILE_2}.zip", BANDS,
               TARGET_RESOLUTION, FILE_2_IMG_ROOT_NAME)

print("\n---- Plotting outputs -----")
plotOutputBands(ZARRFILE, BANDS, OUTPUT_IMG_ROOT_NAME)
