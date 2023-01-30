from typing import Dict
import re

from models.request.datacube_build import DatacubeBuildRequest
from models.request.rasterProductType import RasterProductType


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
