#!/bin/sh

curl -X POST -H "Content-Type: application/json" -d '{
    "rasterCompositions": [
        {
            "rasterFormat": "Sentinel2-2A",
            "rasterPath": "gs://gisaia-arlasea/S2A_MSIL2A_20221017T105041_N0400_R051_T30TXN_20221017T170159",
            "rasterTimestamp": 1665964800
        }
    ],
    "dataCubePath": "gs://gisaia-datacube/S2A_MSIL2A_20221017T105041_N0400_R051_T30TXN_20221017T170159_B01",
    "roi": "-1.17,42.37,-0.32,43.85",
    "bands": ["B01"],
    "targetResolution": 60
    }' http://localhost:5000/cube/build