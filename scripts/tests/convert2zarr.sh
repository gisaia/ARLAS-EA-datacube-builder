#!/bin/sh

curl -X POST -H "Content-Type: application/json" -d '{
    "rasterFiles": [
        {
            "rasterFormat": "Sentinel2-2A",
            "rasterPath": "gs://gisaia-arlasea/S2A_MSIL2A_20221017T105041_N0400_R051_T30TXN_20221017T170159"
        }
    ],
    "zarrFile": "./output/zarr/post",
    "roi": "640000.0,4720000.0,700000.0,4780000.0",
    "bands": ["B01"]
    }' http://localhost:5000/raster2zarr/convert