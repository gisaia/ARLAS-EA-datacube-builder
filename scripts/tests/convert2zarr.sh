#!/bin/sh

curl -X POST -H "Content-Type: application/json" -d '{
    "rasterFile": "./data/soilClassificationwithMachineLearningwithPythonScikitLearn.zip",
    "zarrFile": "./output/zarr/post",
    "roi": "383700.0,8642300.0,397400.0,8651200.0",
    "bands": ["B01", "B02", "B03", "B04"]
    }' http://localhost:5000/raster2zarr/convert