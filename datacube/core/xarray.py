import xarray as xr
from pydantic import BaseModel


def coarse_bands(datacube: xr.Dataset, bands: list[str],
                 x_factor: int, y_factor: int) -> xr.Dataset:
    """
    Mean coarse the bands of a datacube

    :param band A xarray data array
    :param x_factor A coarsing factor along the x dimension
    :param y_factor A coarsing factor along the y dimension
    """
    return datacube.get(bands) \
        .coarsen({"x": x_factor, "y": y_factor}, boundary="pad").mean()


class MinMax(BaseModel):
    min: float
    max: float


def get_approximate_quantile(band: xr.DataArray,
                             quantile: float = 0.02) -> MinMax:
    """
    Coarse a band along all dimensions to find its
    approximate quantile.

    :param band A xarray data array
    :param x_factor A coarsing factor along the x dimension
    :param y_factor A coarsing factor along the y dimension
    :param quantile The quantile to compute. Needs to be between 0 and 1
    """
    if quantile < 0 or quantile > 1:
        raise ValueError("quantile needs to be between 0 and 1" +
                         f"(value given: {quantile})")

    dims = list(band.sizes.keys())

    min, max = band.chunk({dim: -1 for dim in dims}) \
                   .quantile([quantile, 1-quantile], dim=dims).values

    return MinMax(min=min, max=max)
