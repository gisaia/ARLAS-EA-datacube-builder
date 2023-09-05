import base64

# Necessary for the .rio to work
import rioxarray  # noqa F401
import xarray as xr
from matplotlib import cm
from PIL import Image

from datacube.core.models.enums import RGB
from datacube.core.xarray import MinMax, coarse_bands, get_approximate_quantile


def prepare_visualisation(datacube: xr.Dataset, bands: list[str],
                          size: tuple[int, int] = [256, 256]) \
                            -> tuple[xr.Dataset, dict[str, MinMax]]:
    """
    Prepare a datacube for visualisation by coarsing it to fit the input size,
    and compute the 2nd and 98th centile for data clipping.
    This method should be used before any create preview method.
    """
    # Factor to resize the image
    x_factor = len(datacube.x) // size[0]
    y_factor = len(datacube.y) // size[1]

    coarsed_datacube = coarse_bands(datacube, bands,
                                    x_factor, y_factor)

    # Per band, find the 2nd and 98th centile
    clip_values: dict[str, MinMax] = {}
    for band in bands:
        clip_values[band] = get_approximate_quantile(
            coarsed_datacube.get(band), 0.02)

    return coarsed_datacube, clip_values


def __resize_band(dataset: xr.Dataset, band_name: str, time_slice: int,
                  min: float, max: float) -> xr.DataArray:
    """
    Clip a band value between min and max,
    then normalize them between 0 and 255
    """
    band: xr.DataArray = dataset[band_name].sel(t=time_slice)

    """ Clip the highest and lowest values """
    band = xr.where(band > max, max, band)
    band = xr.where(band < min, min, band)

    """ Normalize values within [0-255] """
    band = ((band - min) * 255.0 / (max - min)).astype('uint8')
    return band.transpose().reindex(y=band.y[::-1])


def create_preview_b64(datacube: xr.Dataset, bands: dict[RGB, str],
                       preview_path: str, clip_values: dict[str, MinMax],
                       time_slice: float = None,
                       size: tuple[int, int] = [256, 256]):
    """
    Create a RGB preview of a datacube and convert it to base64
    """
    if time_slice is None:
        time_slice = datacube.get("t").values[-1]

    overview_data = xr.Dataset()
    for color, band in bands.items():
        overview_data[color.value] = __resize_band(
            datacube, band, time_slice,
            clip_values[band].min, clip_values[band].max)

    xlen = len(overview_data.x)
    ylen = len(overview_data.y)
    overview_data = overview_data.isel(
        x=slice(int((xlen-size[1])/2), int((xlen+size[1])/2)),
        y=slice(int((ylen-size[0])/2), int((ylen+size[0])/2)))

    overview_data.rio.to_raster(f"{preview_path}", driver="PNG")
    overview_data.close()
    del overview_data

    # encode in base64
    with open(preview_path, 'rb') as fb:
        b64_image = base64.b64encode(fb.read()).decode('utf-8')

    return b64_image


def create_preview_b64_cmap(datacube: xr.Dataset, preview: dict[str, str],
                            preview_path: str, clip_values: dict[str, MinMax],
                            time_slice: float = None,
                            size: tuple[int, int] = [256, 256]):
    """
    Create a color map preview of a datacube and convert it to base64
    """
    if time_slice is None:
        time_slice = datacube.get("t").values[-1]
    cmap, band = list(preview.items())[0]

    data = __resize_band(datacube, band, time_slice,
                         clip_values[band].min, clip_values[band].max).values

    xlen = data.shape[0]
    ylen = data.shape[1]
    data = data[int((xlen-size[1])/2):int((xlen+size[1])/2),
                int((ylen-size[0])/2):int((ylen+size[0])/2)]

    img = Image.fromarray(cm.get_cmap(cmap)(data, bytes=True))
    try:
        img.save(preview_path)
    except OSError:
        img.convert('RGB').save(preview_path)

    return image_to_base64(preview_path)


def image_to_base64(img_path: str):
    """
    Return a base64 encoded string of the given image/gif
    """
    with open(img_path, 'rb') as fb:
        b64_image = base64.b64encode(fb.read()).decode('utf-8')

    return b64_image
