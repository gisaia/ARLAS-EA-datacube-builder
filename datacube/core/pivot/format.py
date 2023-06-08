import datetime
import json
import os
import os.path as path
import random
import shutil
import string
import tarfile
from pathlib import Path

# Useful for getting the nodata of the band
import rioxarray
import xarray as xr
from pyproj import CRS

from datacube.core.geo.utils import bbox2polygon
from datacube.core.models.metadata import DatacubeMetadata
from datacube.core.models.request.cubeBuild import ExtendedCubeBuildRequest
from datacube.core.pivot.models.catalogue import (Band, CatalogueDescription,
                                                  Polygon, Properties)


def unique_id(size):
    chars = list(set(string.ascii_lowercase + string.digits))
    return ''.join(random.choices(chars, k=size))


def band_to_STAC_raster_band(band: xr.DataArray) -> Band:
    return Band(data_type=band.dtype.name,
                nodata=band.rio.nodata)


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
    creation_time = datetime.datetime.now().isoformat(sep='T')[:-7] \
        .replace('-', '').replace(':', '')
    uid = unique_id(4)
    id = f"MMI_MULT_DCP_{creation_time}_{uid}"

    # Get useful information to build the pivot file
    datacube = xr.open_zarr(datacube_path)
    xmin = datacube.get('x').min().values.tolist()
    xmax = datacube.get('x').max().values.tolist()
    ymin = datacube.get('y').min().values.tolist()
    ymax = datacube.get('y').max().values.tolist()
    bands = ''.join(list(datacube.data_vars.keys()))
    raster_bands = [
        band_to_STAC_raster_band(b) for b in datacube.data_vars.values()]
    datacube.close()

    # In a folder PRODUCT_<ID>
    pivot_root_folder = path.join(str(Path(datacube_path).parent),
                                  f"PRODUCT_{id}")
    os.mkdir(pivot_root_folder)

    # Create catalogue CAT_<ID>.json file
    x, y = bbox2polygon(xmin, ymin, xmax, ymax).exterior.coords.xy
    geometry = Polygon(coordinates=[[x[i], y[i]] for i in range(len(x))])
    properties = Properties(**{
        **metadata.dict(by_alias=True),
        "proj:epsg": CRS.from_string(request.target_projection).to_epsg(),
        "raster:bands": raster_bands
    })
    catalogue = CatalogueDescription(id=id, collection="DOX",
                                     bbox=[xmin, ymin, xmax, ymax],
                                     geometry=geometry,
                                     properties=properties)
    with open(path.join(pivot_root_folder, f"CAT_{id}.json"), 'w') as f:
        f.write(json.dumps(catalogue.dict(by_alias=True), indent=2))

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
