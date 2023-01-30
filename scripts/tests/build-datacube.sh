#!/bin/sh

curl -X POST -H "Content-Type: application/json" -d '{
    "composition": [
        {
            "rasters": [
                {
                    "type": {
                        "format": "2A-Theia",
                        "source": "Sentinel2"
                    },
                    "path": "gs://gisaia-arlasea/SENTINEL2B_20221201-105915-059_L2A_T30TYN_D",
                    "id": 1
                },
                {
                    "type": {
                        "format": "2A-Safe",
                        "source": "Sentinel2"
                    },
                    "path": "gs://gisaia-arlasea/S2A_MSIL2A_20221017T105041_N0400_R051_T30TXN_20221017T170159.SAFE.zip",
                    "id": "2"
                }
            ],
            "timestamp": 1669892355
        },
        {
            "rasters": [
                {
                    "type": {
                        "format": "2A-Theia",
                        "source": "Sentinel2"
                    },
                    "path": "gs://gisaia-arlasea/SENTINEL2B_20221214-110910-728_L2A_T30TYN_D",
                    "id": "3"
                },
                {
                    "type": {
                        "format": "2A-Theia",
                        "source": "Sentinel2"
                    },
                    "path": "gs://gisaia-arlasea/SENTINEL2B_20221214-110914-455_L2A_T30TXN_D",
                    "id": "4"
                }
            ],
            "timestamp": 1671016150
        },
        {
            "rasters": [
                {
                    "type": {
                        "format": "2A-Theia",
                        "source": "Sentinel2"
                    },
                    "path": "gs://gisaia-arlasea/SENTINEL2B_20221224-110912-094_L2A_T30TYN_D",
                    "id": "5"
                },
                {
                    "type": {
                        "format": "2A-Theia",
                        "source": "Sentinel2"
                    },
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
            "name": "S2Theia.B5",
            "description": "This is a description"
        },
        {
            "name": "S2Safe.B05"
        }
    ],
    "targetResolution": 20,
    "aliases": {
        "S2Theia": ["Sentinel2", "2A-Theia"],
        "S2Safe": ["Sentinel2", "2A-Safe"]
    }
}' http://localhost:5000/cube/build
