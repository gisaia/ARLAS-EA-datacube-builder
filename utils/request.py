from typing import Dict, List, Type, Match
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
    aliasProduct = ""
    for k, v in request.aliases.items():
        if v == productType:
            aliasProduct = k
            break
    if aliasProduct == "":
        raise Exception("No alias given for this product type")

    productBands = {}
    for band in request.bands:
        # Extract the bands required from the expression
        match = re.findall(rf'{aliasProduct}\.([a-zA-Z0-9]*)',
                           band.value)
        for m in match:
            productBands[f'{aliasProduct}.{m}'] = m

    return productBands


def getEvalFormula(bandValue: str, aliases: Dict[str, List[str]]) -> str:
    def repl(match: Match[str]) -> str:
        for m in match.groups():
            return f"datacube.get('{m}')"

    result = bandValue
    for alias in aliases.keys():
        result = re.sub(rf"({alias}\.[a-zA-Z0-9]*)", repl, result)

    return result


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
