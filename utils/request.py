from typing import Dict, Type
import re

from models.request.datacube_build import DatacubeBuildRequest
from models.request.rasterProductType import RasterProductType
from models.errors import BadRequest
from models.rasterDrivers import AbstractRasterArchive, \
                                 Sentinel2_Level2A_Safe, \
                                 Sentinel2_Level2A_Theia, \
                                 Sentinel1_Theia, \
                                 Sentinel1_Level1_Safe, \
                                 TheiaSnow


def getProductBands(request: DatacubeBuildRequest,
                    productType: RasterProductType) -> Dict[str, str]:
    """
    Based on the request, creates a dictionnary with the pair
    (datacube name, band name) as (key, value)
    """
    # Extract from the request which bands are required
    for k, v in request.aliases.items():
        if v == productType:
            aliasProduct = k
            break
    productBands = {}
    for band in request.bands:
        # If no value, the name must be 'alias.band'
        if band.value is None:
            alias, band_name = band.name.split(".", 1)
            if alias == aliasProduct:
                productBands[band.name] = band_name
        # If a value is given we need to extract the bands required
        # from the expression
        else:
            match = re.findall(r'datacube\[[\'|\"](.*?)[\'|\"]\]',
                               band.value)
            for m in match:
                alias, band_name = band.name.split(".", 1)
                if alias == aliasProduct:
                    productBands[m] = band_name

            match = re.findall(r'datacube\.get\([\'|\"](.*?)[\'|\"]\)',
                               band.value)
            for m in match:
                alias, band_name = band.name.split(".", 1)
                if alias == aliasProduct:
                    productBands[m] = band_name

    return productBands


def getRasterDriver(rasterProductType) -> Type[AbstractRasterArchive]:
    if rasterProductType == Sentinel2_Level2A_Safe.PRODUCT_TYPE:
        return Sentinel2_Level2A_Safe
    elif rasterProductType == Sentinel2_Level2A_Theia.PRODUCT_TYPE:
        return Sentinel2_Level2A_Theia
    elif rasterProductType == Sentinel1_Theia.PRODUCT_TYPE:
        return Sentinel1_Theia
    elif rasterProductType == Sentinel1_Level1_Safe.PRODUCT_TYPE:
        return Sentinel1_Level1_Safe
    elif rasterProductType == TheiaSnow.PRODUCT_TYPE:
        return TheiaSnow
    else:
        raise BadRequest(
            f"Archive type '{rasterProductType}' does not have a driver")
