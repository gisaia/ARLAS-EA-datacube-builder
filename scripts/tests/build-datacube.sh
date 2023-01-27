#!/bin/sh

curl -X POST -H "Content-Type: application/json" -d '{
    "composition": [
        {
            "rasters": [
                {
                    "format": "2A-Theia",
                    "source": "Sentinel2",
                    "path": "gs://gisaia-arlasea/SENTINEL2B_20221201-105915-059_L2A_T30TYN_D",
                    "id": "1"
                },
                {
                    "format": "2A-Theia",
                    "source": "Sentinel2",
                    "path": "gs://gisaia-arlasea/SENTINEL2B_20221201-105917-780_L2A_T30TXN_D",
                    "id": "2"
                }
            ],
            "timestamp": 1669892355
        },
        {
            "rasters": [
                {
                    "format": "2A-Theia",
                    "source": "Sentinel2",
                    "path": "gs://gisaia-arlasea/SENTINEL2B_20221214-110910-728_L2A_T30TYN_D",
                    "id": "3"
                },
                {
                    "format": "2A-Theia",
                    "source": "Sentinel2",
                    "path": "gs://gisaia-arlasea/SENTINEL2B_20221214-110914-455_L2A_T30TXN_D",
                    "id": "4"
                }
            ],
            "timestamp": 1671016150
        },
        {
            "rasters": [
                {
                    "format": "2A-Theia",
                    "source": "Sentinel2",
                    "path": "gs://gisaia-arlasea/SENTINEL2B_20221224-110912-094_L2A_T30TYN_D",
                    "id": "5"
                },
                {
                    "format": "2A-Theia",
                    "source": "Sentinel2",
                    "path": "gs://gisaia-arlasea/SENTINEL2B_20221224-110915-819_L2A_T30TXN_D",
                    "id": "6"
                }
            ],
            "timestamp": 1671880152
        }
    ],
    "dataCubePath": "test_theia",
    "roi": "-0.661998,42.761697,-0.229943,43.106591",
    "bands": [
        {
            "name": "B5",
            "description": "This is a description"
        }
    ],
    "targetResolution": 20
}' http://localhost:5000/cube/build
