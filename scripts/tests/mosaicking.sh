#!/bin/sh

curl -X POST -H "Content-Type: application/json" -d '{
    "rasterFiles": [
        {
            "rasterFormat": "Sentinel2-2A",
            "rasterPath": "gs://gisaia-arlasea/S2A_MSIL2A_20221017T105041_N0400_R051_T30TYN_20221017T170159",
            "rasterTimestamp": 1662249600
        },
        {
            "rasterFormat": "Sentinel2-2A",
            "rasterPath": "gs://gisaia-arlasea/S2A_MSIL2A_20221017T105041_N0400_R051_T30TXN_20221017T170159",
            "rasterTimestamp": 1662249600
        },
        {
            "rasterFormat": "Sentinel2-2A",
            "rasterPath": "gs://gisaia-arlasea/S2A_MSIL2A_20221017T105041_N0400_R051_T30TXN_20221017T170159",
            "rasterTimestamp": 1662249700
        }
        
    ],
    "dataCubePath": "gs://gisaia-datacube/mosaicking",
    "roi": "-1.17,42.5,0.5,43.85",
    "bands": ["B01"],
    "targetResolution": 20
    }' http://localhost:5000/datacube/build