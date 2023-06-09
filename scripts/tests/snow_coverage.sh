#!/bin/sh

curl -X POST -H "Content-Type: application/json" -d '{
    "composition": [
        {
            "rasters": [
                {
                    "type": {
                        "format": "Snow",
                        "source": "Theia"
                    },
                    "path": "gs://gisaia-arlasea/MULTISAT_20170901-000000-000_L3B-SNOW_T30TXN_D",
                    "id": "snowCoverage2017_T30TXN"
                },
                {
                    "type": {
                        "format": "Snow",
                        "source": "Theia"
                    },
                    "path": "gs://gisaia-arlasea/MULTISAT_20170901-000000-000_L3B-SNOW_T30TYN_D",
                    "id": "snowCoverage2017_T30TYN"
                }
            ],
            "timestamp": 1504224000
        },
        {
            "rasters": [
                {
                    "type": {
                        "format": "Snow",
                        "source": "Theia"
                    },
                    "path": "gs://gisaia-arlasea/MULTISAT_20180901-000000-000_L3B-SNOW_T30TXN_D",
                    "id": "snowCoverage2018_T30TXN"
                },
                {
                    "type": {
                        "format": "Snow",
                        "source": "Theia"
                    },
                    "path": "gs://gisaia-arlasea/MULTISAT_20180901-000000-000_L3B-SNOW_T30TYN_D",
                    "id": "snowCoverage2018_T30TYN"
                }
            ],
            "timestamp": 1535760000
        },
        {
            "rasters": [
                {
                    "type": {
                        "format": "Snow",
                        "source": "Theia"
                    },
                    "path": "gs://gisaia-arlasea/MULTISAT_20190901-000000-000_L3B-SNOW_T30TXN_D",
                    "id": "snowCoverage2019_T30TXN"
                },
                {
                    "type": {
                        "format": "Snow",
                        "source": "Theia"
                    },
                    "path": "gs://gisaia-arlasea/MULTISAT_20190901-000000-000_L3B-SNOW_T30TYN_D",
                    "id": "snowCoverage2019_T30TYN"
                }
            ],
            "timestamp": 1567296000
        },
        {
            "rasters": [
                {
                    "type": {
                        "format": "Snow",
                        "source": "Theia"
                    },
                    "path": "gs://gisaia-arlasea/MULTISAT_20200901-000000-000_L3B-SNOW_T30TXN_D",
                    "id": "snowCoverage2020_T30TXN"
                },
                {
                    "type": {
                        "format": "Snow",
                        "source": "Theia"
                    },
                    "path": "gs://gisaia-arlasea/MULTISAT_20200901-000000-000_L3B-SNOW_T30TYN_D",
                    "id": "snowCoverage2020_T30TYN"
                }
            ],
            "timestamp": 1598918400
        }
    ],
    "datacube_path": "snowCoveragePyrenees",
    "roi": "-1.774729,42.329373,0.788877,43.353336",
    "bands": [
        {
            "name": "SCD",
            "value": "Snow.SCD / 365",
            "description": "Snow Coverage Duration",
            "unit": "% of the year"
        }
    ],
    "target_resolution": 20,
    "aliases": [
        {
            "alias": "Snow",
            "source": "Theia",
            "format": "Snow"
        }
    ]
}' http://localhost:8080/cube/build
