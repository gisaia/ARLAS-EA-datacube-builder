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

To start the service with python, execute the `app.py` file.
Parameters can be set with the file `configs/app.conf.yml`, that has the following values by default:

```yaml
dc3-builder:
  host: "localhost"
  port: 5000
  debug: True
```

The output datacubes and previews can be configured to be written either locally or in an object store through the `storage` parameter of the `configs/outputObjectStore.yml` file. Several options are available:

- "local" to write locally
- "gs" to write in Google Cloud Storage

In order to be able to access Object Stores, an `credentials` file must be created to set the global variables used.

```yaml
GS_INPUT_BUCKET=
GS_INPUT_PRIVATE_KEY_ID=
GS_INPUT_PRIVATE_KEY=
GS_INPUT_CLIENT_EMAIL=

GS_OUTPUT_BUCKET=
GS_OUTPUT_PRIVATE_KEY_ID=
GS_OUTPUT_PRIVATE_KEY=
GS_OUTPUT_CLIENT_EMAIL=
```

The script `scripts/start-app.sh` is available as an example of how to launch the service.

## Running ARLAS-datacube-builder with docker

### Building the image

```shell
export DOCKER_DEFAULT_PLATFORM=linux/amd64 # For MacOSX
docker build -t gisaia/arlas-datacube-builder:latest .
```

### Starting the REST Service

When using docker to launch the service, the app will be configured using the `docker.app.conf.yml` file.
The app can be configured the same way as locally, but is pre-configured to work as is.
For the app to work, Hazelcast's host needs to be replaced by the host machine address that will be used for the Hazelcast communication.

```shell
docker compose up
```

### Caching data

It is possible to start the REST service with data already available, by using the tmp folder where requested files will be downloaded. By default, the directory used is `$PWD/tmp/` as specified in the `docker-compose.yaml` file, but can be changed to where your data is stored.

The files need to be stored as they would be when extracted from their archive.