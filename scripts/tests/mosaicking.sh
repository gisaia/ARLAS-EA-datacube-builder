#!/bin/sh

curl -X POST -H "Content-Type: application/json" -d '{
    "composition": [
        {
            "rasters": [
                {
                    "format": "2A",
                    "source": "Sentinel2",
                    "path": "gs://gisaia-arlasea/S2A_MSIL2A_20221017T105041_N0400_R051_T30TYN_20221017T170159"
                },
                {
                    "format": "2A",
                    "source": "Sentinel2",
                    "path": "gs://gisaia-arlasea/S2A_MSIL2A_20221017T105041_N0400_R051_T30TXN_20221017T170159"
                }
            ],
            "timestamp": 1662249600
        },
        {
            "rasters": [
                {
                    "format": "2A",
                    "source": "Sentinel2",
                    "path": "gs://gisaia-arlasea/S2A_MSIL2A_20221017T105041_N0400_R051_T30TXN_20221017T170159"
                }
            ],
            "timestamp": 1662249700
        }
        
    ],
    "dataCubePath": "mosaicking",
    "roi": "-1.17,42.5,0.5,43.85",
    "bands": ["B01"],
    "targetResolution": 20
    }' http://localhost:5000/cube/build