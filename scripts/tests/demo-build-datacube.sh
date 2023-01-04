#!/bin/sh

curl -X POST -H "Content-Type: application/json" -d '{
    "rasterCompositions": [
        {
            "rasterFormat": "Sentinel2-2A",
            "rasterPath": "gs://gisaia-arlasea/S2A_MSIL2A_20220910T105631_N0400_R094_T30TXN_20220910T171600",
            "rasterTimestamp": 1662768000
        },
        {
            "rasterFormat": "Sentinel2-2A",
            "rasterPath": "gs://gisaia-arlasea/S2A_MSIL2A_20220920T105741_N0400_R094_T30TXN_20220920T171559",
            "rasterTimestamp": 1663632000
        },
        {
            "rasterFormat": "Sentinel2-2A",
            "rasterPath": "gs://gisaia-arlasea/S2B_MSIL2A_20220905T105619_N0400_R094_T30TXN_20220905T123225",
            "rasterTimestamp": 1662336000
        },
        {
            "rasterFormat": "Sentinel2-2A",
            "rasterPath": "gs://gisaia-arlasea/S2B_MSIL2A_20220925T105709_N0400_R094_T30TXN_20220925T134749",
            "rasterTimestamp": 1664064000
        },
        {
            "rasterFormat": "Sentinel2-2A",
            "rasterPath": "gs://gisaia-arlasea/S2B_MSIL2A_20221005T105819_N0400_R094_T30TXN_20221005T135951",
            "rasterTimestamp": 1664928000
        }
    ],
    "dataCubePath": "gs://gisaia-datacube/demo_datacube",
    "roi": "-1.738586,42.688794,-1.505968,42.87091",
    "bands": ["B05"],
    "targetResolution": 20
    }' http://localhost:5000/cube/build