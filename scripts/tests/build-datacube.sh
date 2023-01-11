#!/bin/sh

curl -X POST -H "Content-Type: application/json" -d '{
    "composition": [
        {
            "rasters": [
                {
                    "format": "2A-Theia",
                    "source": "Sentinel2",
                    "path": "gs://gisaia-arlasea/SENTINEL2B_20221201-105915-059_L2A_T30TYN_D"
                },
                {
                    "format": "2A-Theia",
                    "source": "Sentinel2",
                    "path": "gs://gisaia-arlasea/SENTINEL2B_20221201-105917-780_L2A_T30TXN_D"
                }
            ],
            "timestamp": 1669892355000
        },
        {
            "rasters": [
                {
                    "format": "2A-Theia",
                    "source": "Sentinel2",
                    "path": "gs://gisaia-arlasea/SENTINEL2B_20221214-110910-728_L2A_T30TYN_D"
                },
                {
                    "format": "2A-Theia",
                    "source": "Sentinel2",
                    "path": "gs://gisaia-arlasea/SENTINEL2B_20221214-110914-455_L2A_T30TXN_D"
                }
            ],
            "timestamp": 1671016150000
        },
        {
            "rasters": [
                {
                    "format": "2A-Theia",
                    "source": "Sentinel2",
                    "path": "gs://gisaia-arlasea/SENTINEL2B_20221224-110912-094_L2A_T30TYN_D"
                },
                {
                    "format": "2A-Theia",
                    "source": "Sentinel2",
                    "path": "gs://gisaia-arlasea/SENTINEL2B_20221224-110915-819_L2A_T30TXN_D"
                }
            ],
            "timestamp": 1671880152000
        }
    ],
    "dataCubePath": "OssauIratyParallel",
    "roi": "Polygon((-0.661998 42.761697, -0.229943 42.761697, -0.229943 43.106591, -0.4 43.2, -0.661998 43.106591, -0.661998 42.761697))",
    "bands": ["B5"],
    "targetResolution": 10,
    "targetProjection": "EPSG:4326"
}' http://localhost:5000/cube/build