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
                    "path": "gs://gisaia-arlasea/MULTISAT_20170901-000000-000_L3B-SNOW_T30TXN_D.zip",
                    "id": "snowCoverage2017_T30TXN"
                },
                {
                    "type": {
                        "format": "Snow",
                        "source": "Theia"
                    },
                    "path": "gs://gisaia-arlasea/MULTISAT_20170901-000000-000_L3B-SNOW_T30TYN_D.zip",
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
                    "path": "gs://gisaia-arlasea/MULTISAT_20180901-000000-000_L3B-SNOW_T30TXN_D.zip",
                    "id": "snowCoverage2018_T30TXN"
                },
                {
                    "type": {
                        "format": "Snow",
                        "source": "Theia"
                    },
                    "path": "gs://gisaia-arlasea/MULTISAT_20180901-000000-000_L3B-SNOW_T30TYN_D.zip",
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
                    "path": "gs://gisaia-arlasea/MULTISAT_20190901-000000-000_L3B-SNOW_T30TXN_D.zip",
                    "id": "snowCoverage2019_T30TXN"
                },
                {
                    "type": {
                        "format": "Snow",
                        "source": "Theia"
                    },
                    "path": "gs://gisaia-arlasea/MULTISAT_20190901-000000-000_L3B-SNOW_T30TYN_D.zip",
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
                    "path": "gs://gisaia-arlasea/MULTISAT_20200901-000000-000_L3B-SNOW_T30TXN_D.zip",
                    "id": "snowCoverage2020_T30TXN"
                },
                {
                    "type": {
                        "format": "Snow",
                        "source": "Theia"
                    },
                    "path": "gs://gisaia-arlasea/MULTISAT_20200901-000000-000_L3B-SNOW_T30TYN_D.zip",
                    "id": "snowCoverage2020_T30TYN"
                }
            ],
            "timestamp": 1598918400
        }
    ],
    "dataCubePath": "snowCoveragePyrenees",
    "roi": "-1.774729,42.329373,0.788877,43.353336",
    "bands": [
        {
            "name": "Snow.SCD",
            "description": "Snow Coverage Duration"
        }
    ],
    "targetResolution": 20,
    "aliases": {
        "Snow": ["Theia", "Snow"]
    }
}' http://localhost:5000/cube/build
