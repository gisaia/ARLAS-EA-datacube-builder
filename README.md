# ARLAS-datacube-builder

## About

ARLAS-datacube-builder is a REST service for building datacube from RASTER sources.

Supported sources are:
- sentinel-2 level 2a
    - SAFE Format
    - THEIA Format

## Prerequisites

Docker or python3

## Running ARLAS-datacube-builder with python

## Running ARLAS-datacube-builder with docker

### Building the image

```shell
export DOCKER_DEFAULT_PLATFORM=linux/amd64 # For MacOSX
docker build -t arlas-datacube-builder:latest .
```

### Starting the REST Service

```shell
docker run --env-file credentials \
    -p 8080:5000 \
    arlas-datacube-builder:latest
```
