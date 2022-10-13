#!/bin/sh

curl -X POST -H "Content-Type: application/json" -d '{
    "rasterFile": "./data/soilClassificationwithMachineLearningwithPythonScikitLearn/S2B_MSIL1C_20200917T151709_N0209_R125_T18LUM_20200917T203629.SAFE/GRANULE/L1C_T18LUM_A018455_20200917T151745/IMG_DATA/T18LUM_20200917T151709_B01.jp2",
    "zarrFile": "./output/zarr/post"
    }' http://localhost:5000/raster2zarr/convert