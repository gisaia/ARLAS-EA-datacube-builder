# ARLAS-datacube-builder

## About

ARLAS-datacube-builder is a REST service for building datacube from RASTER sources.

Supported product types are:

| Product type                      | Source    | Format    |
|-----------------------------------|-----------|-----------|
| Sentinel2 Level 2A SAFE archive   | Sentinel2 | L2A-SAFE  |
| Sentinel2 Level 2A Theia product  | Sentinel2 | L2A-Theia |
| Sentinel1 Theia product           | Sentinel1 | Theia     |
| Sentinel1 Level 1 SAFE archive    | Sentinel1 | L1-SAFE   |
| Theia Snow coverage product       | Theia     | Snow      |

When running the service, a swagger of the API is available at the path `/docs` of the service on the dedicated port.

## Prerequisites

Docker or python3

## Running ARLAS-datacube-builder with python

To start the service with python, execute the `app.py` file with the following optional options:
- `--debug`: launch the debug mode
- `--host HOST_IP`: set the host IP of the service, by default `127.0.0.1`
- `--port PORT`: set the port of the service, by default `5000`

In order to be able to access Object Stores, an `env.sh` file must be created to set the global variables used.

```shell
#!/bin/sh

export GS_INPUT_BUCKET=
export GS_INPUT_PRIVATE_KEY_ID=
export GS_INPUT_PRIVATE_KEY=
export GS_INPUT_CLIENT_EMAIL=

export GS_OUTPUT_BUCKET=
export GS_OUTPUT_PRIVATE_KEY_ID=
export GS_OUTPUT_PRIVATE_KEY=
export GS_OUTPUT_CLIENT_EMAIL=
```

The script `scripts/start-app.sh` is available as an example of how to launch the service.

## Running ARLAS-datacube-builder with docker

### Building the image

```shell
export DOCKER_DEFAULT_PLATFORM=linux/amd64 # For MacOSX
docker build -t gisaia/arlas-datacube-builder:latest .
```

### Starting the REST Service

```shell
docker run --env-file credentials \
    -p 8080:{port} \
    gisaia/arlas-datacube-builder:latest
```

### Caching data

It is possible to start the REST service with data already available, by using the tmp folder where requested files will be downloaded. In order to do so, one can mount a volume containing them as below.

```shell
docker run --env-file credentials \
    -p 8080:{port} \
    -v /ABSOLUTE/PATH/TO/DATA/:/app/tmp \
    gisaia/arlas-datacube-builder:latest
```

The files need to be put in the `tmp` folder as they would be when extracted from their archive.