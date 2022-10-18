#!/bin/sh

curl -X POST -H "Content-Type: application/json" -d '{
    "rasterFile": ["Sentinel2-2A:./data/S2A_MSIL2A_20220809T102041_N0400_R065_T32TML_20220809T180703.zip", "Sentinel2-2A:./data/S2B_MSIL2A_20220814T101559_N0400_R065_T32TML_20220814T130923.zip"],
    "zarrFile": "./output/zarr/post",
    "roi": "400000.0,4480000.0,500000.0,4600000.0",
    "bands": ["B01", "B02", "B03", "B04"],
    "targetResolution": 20
    }' http://localhost:5000/raster2zarr/convert