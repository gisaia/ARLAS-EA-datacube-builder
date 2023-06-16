import re
from typing import Match, Type

from datacube.core.models.exception import BadRequest
from datacube.core.models.request.cubeBuild import ExtendedCubeBuildRequest
from datacube.core.models.request.rasterProductType import (AliasedRasterType,
                                                            RasterType)
from datacube.core.rasters.drivers import (AbstractRasterArchive,
                                           Sentinel1_Level1_Safe,
                                           Sentinel1_Theia,
                                           Sentinel2_Level1C_Pivot,
                                           Sentinel2_Level2A_Safe,
                                           Sentinel2_Level2A_Theia, TheiaSnow)


def get_product_bands(request: ExtendedCubeBuildRequest,
                      product_type: RasterType) -> dict[str, str]:
    """
    Based on the request, creates a dictionnary with the pair
    (datacube name, band name) as (key, value)
    """
    # Extract from the request which bands are required
    alias_product = ""
    for alias in request.aliases:
        if RasterType(**alias.dict()) == product_type:
            alias_product = alias.alias
            break
    if alias_product == "":
        raise Exception(f"No alias given for product type {product_type}")

    product_bands = {}
    for band in request.bands:
        # Extract the bands required from the expression
        match = re.findall(rf'{alias_product}\.([a-zA-Z0-9]*)',
                           band.expression)
        for m in match:
            product_bands[f'{alias_product}.{m}'] = m

    return product_bands


def get_eval_formula(band_expression: str,
                     aliases: list[AliasedRasterType]) -> str:
    """
    Transform the requested expression of the band in a xarray operation
    """
    def repl(match: Match[str]) -> str:
        for m in match.groups():
            return f"datacube.get('{m}')"

    result = band_expression
    for alias in map(lambda a: a.alias, aliases):
        result = re.sub(rf"({alias}\.[a-zA-Z0-9]*)", repl, result)

    return result


def get_raster_driver(raster_product_type: RasterType) \
        -> Type[AbstractRasterArchive]:
    if raster_product_type == Sentinel2_Level2A_Safe.PRODUCT_TYPE:
        return Sentinel2_Level2A_Safe
    elif raster_product_type == Sentinel2_Level2A_Theia.PRODUCT_TYPE:
        return Sentinel2_Level2A_Theia
    elif raster_product_type == Sentinel1_Theia.PRODUCT_TYPE:
        return Sentinel1_Theia
    elif raster_product_type == Sentinel1_Level1_Safe.PRODUCT_TYPE:
        return Sentinel1_Level1_Safe
    elif raster_product_type == TheiaSnow.PRODUCT_TYPE:
        return TheiaSnow
    elif raster_product_type == Sentinel2_Level1C_Pivot.PRODUCT_TYPE:
        return Sentinel2_Level1C_Pivot
    else:
        raise BadRequest(
            f"Archive type '{raster_product_type}' does not have a driver")
