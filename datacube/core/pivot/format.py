import json
import os
import os.path as path
import random
import re
import shutil
import string
import tarfile
from datetime import datetime
from pathlib import Path

# Useful for getting the nodata of the band
import rioxarray
import xarray as xr
from pyproj import CRS

from datacube.core.geo.utils import bbox2polygon
from datacube.core.models.metadata import DatacubeMetadata
from datacube.core.models.request.cubeBuild import ExtendedCubeBuildRequest
from datacube.core.pivot.models.catalog import (Band, CatalogDescription,
                                                Polygon, Properties,
                                                SensorFamily)
from datacube.core.utils import get_raster_driver


def unique_id(size):
    chars = list(set(string.ascii_lowercase + string.digits))
    return ''.join(random.choices(chars, k=size))


def band_to_STAC_raster_band(band: xr.DataArray) -> Band:
    return Band(data_type=band.dtype.name,
                nodata=str(band.rio.nodata))


def pivot_format_datacube(request: ExtendedCubeBuildRequest,
                          datacube_path: str,
                          preview_path: str,
                          metadata: DatacubeMetadata) -> tuple[str, str]:
    """
    Transforms the datacube in the Pivot archive format.
    Returns the path to the tarred Pivot archive and
    the name of the preview file.
    """
    # Create the unique id following PFD specifications
    creation_time = datetime.now().isoformat(timespec='seconds') \
        .replace('-', '').replace(':', '')
    uid = unique_id(4)
    id = f"MMI_MULT_DCP_{creation_time}_{uid}"

    # Get useful information to build the pivot file
    datacube = xr.open_zarr(datacube_path)
    xmin = datacube.get('x').min().values.tolist()
    xmax = datacube.get('x').max().values.tolist()
    ymin = datacube.get('y').min().values.tolist()
    ymax = datacube.get('y').max().values.tolist()
    tmin = datacube.get('t').min().values.tolist()
    tmax = datacube.get('t').max().values.tolist()
    bands = ''.join(list(datacube.data_vars.keys()))
    raster_bands = [
        band_to_STAC_raster_band(b) for b in datacube.data_vars.values()]
    datacube.close()

    # In a folder PRODUCT_<ID>
    pivot_root_folder = path.join(str(Path(datacube_path).parent),
                                  f"PRODUCT_{id}")
    os.mkdir(pivot_root_folder)

    # Find sensor family
    datacube_sensor = None
    for alias in request.aliases:
        sensor: SensorFamily = get_raster_driver(alias).SENSOR_TYPE \
            if hasattr(get_raster_driver(alias), "SENSOR_TYPE") \
            else SensorFamily.UNKNOWN
        if not datacube_sensor:
            datacube_sensor = sensor
        else:
            if sensor == SensorFamily.UNKNOWN or \
              datacube_sensor == SensorFamily.UNKNOWN:
                datacube_sensor = SensorFamily.UNKNOWN
            elif sensor != datacube_sensor:
                datacube_sensor = SensorFamily.MULTI

    # Create catalog CAT_<ID>.json file
    x, y = bbox2polygon(xmin, ymin, xmax, ymax).exterior.coords.xy
    geometry = Polygon(coordinates=[[x[i], y[i]] for i in range(len(x))])
    properties = Properties(
        datetime=datetime.now().isoformat(timespec='seconds'),
        start_datetime=datetime.fromtimestamp(tmin).isoformat(),
        end_datetime=datetime.fromtimestamp(tmax).isoformat(),
        **metadata.dict(by_alias=True), **{
            "proj:epsg": CRS.from_string(request.target_projection).to_epsg(),
            "raster:bands": raster_bands,
            "dox:thematics": request.thematics,
            "dox:sensorFamily": datacube_sensor
        }
    )

    title = (request.datacube_path[:-1] if request.datacube_path[-1] == "/"
             else request.datacube_path).split("/")[-1]

    catalog = CatalogDescription(
        title=title, description=request.description, id=id,
        bbox=[xmin, ymin, xmax, ymax], geometry=geometry,
        assets={"datacube": [b for b in datacube.data_vars.keys()]},
        properties=properties)

    with open(path.join(pivot_root_folder, f"CAT_{id}.json"), 'w') as f:
        catalog_dict = catalog.dict(by_alias=True, exclude_none=True)

        properties = {}
        dc_properties = {}
        for k, v in catalog_dict['properties'].items():
            if (not re.match('^dc3', k)) and (not re.match('^cube', k)):
                properties[k] = v
            elif k == 'processing:level':
                properties['processing:product_type'] = v
            else:
                # Replace dc3 with dox_dc3
                dc_properties[re.sub('^dc3', 'dox_dc3', k)] = v

        catalog_dict['properties'] = {**properties, **dc_properties}
        f.write(json.dumps(catalog_dict, indent=2))

    # Rename preview to PREVIEW
    pivot_preview_name = f"PREVIEW_{id}.PNG"
    shutil.copy(preview_path, path.join(pivot_root_folder, pivot_preview_name))

    # Put zarr in folder under the format IMG_DC3_<BANDS>_<ID>.zarr
    image_root_folder = path.join(pivot_root_folder, f"IMAGE_{id}")
    os.mkdir(image_root_folder)
    shutil.copytree(
        datacube_path,
        path.join(image_root_folder,
                  f"IMG_DC3_{bands}_{request.target_resolution}m_{id}.ZARR"))

    # Tar gz archive
    archive_path = path.join(str(Path(datacube_path).parent), f"{id}.TAR")
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(pivot_root_folder, arcname=path.basename(pivot_root_folder))

    # Remove un-tarred folder
    shutil.rmtree(pivot_root_folder)

    return archive_path, pivot_preview_name
