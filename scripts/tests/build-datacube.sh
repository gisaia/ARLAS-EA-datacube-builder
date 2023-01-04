#!/bin/sh

curl -X POST -H "Content-Type: application/json" -d '{
    "rasterCompositions": [
        {
            "rasterFormat": "Sentinel2-2A-Theia",
            "rasterPath": "gs://gisaia-arlasea/SENTINEL2A_20221106-105923-597_L2A_T30TXN_D",
            "rasterTimestamp": 1667732363
        }
    ],
    "dataCubePath": "gs://gisaia-datacube/test_theia",
    "roi": "-1.0,42.688794,-0.5,42.87091",
    "bands": ["B5"],
    "targetResolution": 20
    }' http://localhost:5000/cube/build