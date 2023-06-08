#!/bin/sh

curl -X POST -H "Content-Type: application/json" -d '{
    "composition": [
        {
            "rasters": [
                {
                    "type": {
                        "format": "L1C-Pivot",
                        "source": "Sentinel2"
                    },
                    "path": "gs://gisaia-arlasea/PRODUCT_S2A_MSI__L1C_20180424T110609_3nek.tar",
                    "id": "pivot_1"
                },
                {
                    "type": {
                        "format": "L1C-Pivot",
                        "source": "Sentinel2"
                    },
                    "path": "gs://gisaia-arlasea/PRODUCT_S2A_MSI__L1C_20180424T110609_s62i.tar",
                    "id": "pivot_2"
                }
            ],
            "timestamp": 1504224000
        }
    ],
    "datacube_path": "pivot",
    "roi": "-1.774729,42.329373,0.788877,43.353336",
    "bands": [
        {
            "name": "B02",
            "value": "Pivot.B02"
        }
    ],
    "target_resolution": 10,
    "aliases": [
        {
            "alias": "Pivot",
            "source": "Sentinel2",
            "format": "L1C-Pivot"
        }
    ]
}' http://localhost:8080/cube/build
