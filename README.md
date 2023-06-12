# ARLAS-datacube-builder

## About

ARLAS-datacube-builder is a REST service for building datacube from RASTER sources.

The RASTER sources can be stored locally or in an Object Store.

| Storage      | Possible formats                                          |
|--------------|-----------------------------------------------------------|
| Local        | ./local/path/file<br>~/local/path/file<br>local/path/file |
| Google Cloud | gs://my_bucket/my_blob                                    |

For local storage, paths *have* to be relative.
They can be present only in the local directory that is indicated in the `configs/input.storage.yml` configuration file.
This local directory is automatically prefixed to any local path that are given.

Supported product types are:

| Product type                                | Source    | Format     |
|---------------------------------------------|-----------|------------|
| Sentinel1 Theia product                     | Sentinel1 | Theia      |
| Sentinel1 Level 1 SAFE archive              | Sentinel1 | L1-SAFE    |
| Sentinel2 Level 1C Domino-X PIVOT archive   | Sentinel2 | L1C-PIVOT  |
| Sentinel2 Level 2A SAFE archive             | Sentinel2 | L2A-SAFE   |
| Sentinel2 Level 2A Theia product            | Sentinel2 | L2A-Theia  |
| Theia Snow coverage product                 | Theia     | Snow       |

When running the service, a swagger of the API is available at the path `/docs` of the service on the dedicated port.

The service caches raster metadata in a `cache` folder, that is cleared at the launch as well as as the metadatas are consumed.

## Prerequisites

Docker or python3

## Running ARLAS-datacube-builder with python

To start the service with python and default configuration, execute the `app.py` file.

The script `scripts/start-app.sh` is available as an example of how to launch the service.

## Running ARLAS-datacube-builder with docker

### Building the image

```shell
export DOCKER_DEFAULT_PLATFORM=linux/amd64 # For MacOSX
docker build -t gisaia/arlas-datacube-builder:latest .
```

### Starting the REST Service

To launch the service, simply execute the following command:

```shell
docker compose up
```

### Caching data

It is possible to start the REST service with data already available, by using the tmp folder where requested files will be downloaded. By default, the directory used is `$PWD/tmp/` as specified in the `docker-compose.yaml` file, but can be changed to where your data is stored.

The files need to be stored as they would be when extracted from their archive.

## How to configure ARLAS-datacube-builder

A default configuration is present in the `configs` folder.

### App configuration

Parameters can be set with the file `configs/app.conf.yml`, that has the following structure:

```yaml
dc3-builder:
  host: <HOST>
  port: <PORT>
  debug: <True|False>
```

When using docker to launch the service, the app will be configured using the `docker.app.conf.yml` file.
The app can be configured the same way as locally, but is pre-configured to work as is.

The configuration looks like the following:

```yaml
dc3-builder:
  host: 0.0.0.0
  port: <PORT>
  debug: <True|False>
```

### Input configuration

The file `configs/input.storage.yml` contains the configuration for the different input object stores. It can be used to configure different types of object stores, whether locally or in the cloud, using the following structure:

```yaml
gs:
  bucket: <GS_INPUT_BUCKET>
  api_key:
    private_key_id: <GS_INPUT_PRIVATE_KEY_ID>
    private_key: <GS_INPUT_PRIVATE_KEY>
    client_email: <GS_INPUT_CLIENT_EMAIL>
    token_uri: "https://oauth2.googleapis.com/token"

local:
  root_directory: <LOCAL_ROOT_DIRECTORY>

```

### Output configuration

The output datacubes and previews can be configured to be written either locally or in an object store through the `storage` parameter of the `configs/output.storage.yml` file. Several options are available:

- "local" to write locally
- "gs" to write in Google Cloud Storage

The configuration file has the following structure:

```yaml
storage: <local|gs>
directory: <LOCAL_OUTPUT_DIRECTORY>

bucket: <GS_BUCKET>
api_key:
  private_key_id: <GS_OUTPUT_PRIVATE_KEY_ID>
  private_key: <GS_OUTPUT_PRIVATE_KEY>
  client_email: <GS_OUTPUT_CLIENT_EMAIL>
  token_uri: "https://oauth2.googleapis.com/token"

```

### Credentials

In order to be able to access Object Stores, an `credentials` file must be created to set the global variables used.

```
GS_INPUT_BUCKET=
GS_INPUT_PRIVATE_KEY_ID=
GS_INPUT_PRIVATE_KEY=
GS_INPUT_CLIENT_EMAIL=

GS_OUTPUT_BUCKET=
GS_OUTPUT_PRIVATE_KEY_ID=
GS_OUTPUT_PRIVATE_KEY=
GS_OUTPUT_CLIENT_EMAIL=
```

### Creating datacubes in the Domino-X Pivot format

The service is able to transform the desired datacubes in the Domino-X Pivot format by setting the following parameter in the `configs/app.conf.yml` or `configs/docker.app.conf.yml` file depending on the usage.

It will write either locally or in an object store both the PIVOT archive and the preview.

```yaml
...
dc3-builder:
  ...
  pivot_format: True
...
```
