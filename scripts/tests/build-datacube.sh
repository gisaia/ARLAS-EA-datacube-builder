#!/bin/sh

curl -X POST -H "Content-Type: application/json" -d '{
    "composition": [
        {
            "rasters": [
                {
                    "type": {
                        "format": "Theia",
                        "source": "Sentinel1"
                    },
                    "path": "gs://gisaia-arlasea/MV_S1A_OCCITANIE_20210807T175541.tiff",
                    "id": "occitanie"
                },
                {
                    "type": {
                        "format": "Theia",
                        "source": "Sentinel1"
                    },
                    "path": "gs://gisaia-arlasea/MV_S1B_ESPAGNE-NAVARRE_20210911T180247.tiff",
                    "id": "navarre"
                }
            ],
            "timestamp": 1633259075
        },
        {
            "rasters": [
                {
                    "type": {
                        "format": "L2A-Theia",
                        "source": "Sentinel2"
                    },
                    "path": "gs://gisaia-arlasea/SENTINEL2B_20221201-105915-059_L2A_T30TYN_D",
                    "id": 1
                },
                {
                    "type": {
                        "format": "L2A-SAFE",
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
                        "format": "L2A-Theia",
                        "source": "Sentinel2"
                    },
                    "path": "gs://gisaia-arlasea/SENTINEL2B_20221214-110910-728_L2A_T30TYN_D",
                    "id": "3"
                },
                {
                    "type": {
                        "format": "L2A-Theia",
                        "source": "Sentinel2"
                    },
                    "path": "gs://gisaia-arlasea/SENTINEL2B_20221214-110914-455_L2A_T30TXN_D",
                    "id": "4"
                },
                {
                    "type": {
                        "format": "L1-SAFE",
                        "source": "Sentinel1"
                    },
                    "path": "gs://gisaia-arlasea/S1A_IW_GRDH_1SDV_20221224T175547_20221224T175612_046477_059193_997A.zip",
                    "id": "S1SAFE"
                }
            ],
            "timestamp": 1671016150
        },
        {
            "rasters": [
                {
                    "type": {
                        "format": "L2A-Theia",
                        "source": "Sentinel2"
                    },
                    "path": "gs://gisaia-arlasea/SENTINEL2B_20221224-110912-094_L2A_T30TYN_D",
                    "id": "6"
                },
                {
                    "type": {
                        "format": "L2A-Theia",
                        "source": "Sentinel2"
                    },
                    "path": "gs://gisaia-arlasea/SENTINEL2B_20221224-110915-819_L2A_T30TXN_D",
                    "id": "7"
                }
            ],
            "timestamp": 1671880152
        }
    ],
    "datacube_path": "test_theia",
    "roi": "-0.661998,42.5,0,43",
    "bands": [
        {
            "name": "S2Theia.B5",
            "description": "This is a description",
            "cmap": "viridis"
        },
        {
            "name": "S2Safe.B05"
        },
        {
            "name": "S1Theia.test"
        },
        {
            "name": "S1SAFE.grd-vh",
            "min": 0,
            "max": 1000
        }
    ],
    "target_resolution": 20,
    "aliases": {
        "S2Theia": ["Sentinel2", "L2A-Theia"],
        "S2Safe": ["Sentinel2", "L2A-SAFE"],
        "S1Theia": ["Sentinel1", "Theia"],
        "S1SAFE": ["Sentinel1", "L1-SAFE"]
    }
}' http://localhost:5000/cube/build
