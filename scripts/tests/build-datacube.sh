#!/bin/sh

curl -X POST -H "Content-Type: application/json" -d '{
    "composition": [
        {
            "rasters": [
                {
                    "format": "2A-Theia",
                    "source": "Sentinel2",
                    "path": "gs://gisaia-arlasea/SENTINEL2A_20221106-105923-597_L2A_T30TXN_D"
                }
            ],
            "timestamp": 1667732363
        }
    ],
    "dataCubePath": "test_theia",
    "roi": "-1.0,42.688794,-0.5,42.87091",
    "assets": [
        {
            "name": "RMinusG",
            "value": "datacube.B2 - datacube.B3",
            "rgb": "RED"
        },
        {
            "name": "B4",
            "rgb": "GREEN"
        },
        {
            "name": "NDVI",
            "value": "(datacube.B8 - datacube[\u0027B5\u0027]) / (datacube.B8 + datacube.B5)",
            "rgb": "BLUE"
        }
    ],
    "targetResolution": 20
}' http://localhost:5000/cube/build
