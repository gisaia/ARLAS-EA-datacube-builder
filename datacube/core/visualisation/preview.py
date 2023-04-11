import xarray as xr
import base64
# Apparently necessary for the .rio to work
import rioxarray
from typing import Dict

from PIL import Image, ImageFont, ImageDraw
from matplotlib import cm

from datacube.core.models.enums import RGB

FONT = "./configs/Roboto-Light.ttf"


def __resize_band(dataset: xr.Dataset, band: str, x_factor: int,
                  y_factor: int, time_slice: int) -> xr.DataArray:
    """
    Put a band values between 0 and 255
    """
    band: xr.DataArray = dataset[band].sel(t=time_slice)

    """ Change the resolution """
    band = band.coarsen({"x": x_factor, "y": y_factor}, boundary="pad").mean()

    """ Clip the 2% of highest and lowest values """
    min, max = band.chunk({"x": -1, "y": -1}) \
                   .quantile([0.02, 0.98], dim=["x", "y"]).values
    band = xr.where(band > max, max, band)
    band = xr.where(band < min, min, band)

    """ Normalize values within [0-255] """
    band = ((band - min) * 255.0 / (max - min)).astype('uint8')
    return band.transpose().reindex(y=band.y[::-1])


def create_preview_b64(dataset: xr.Dataset, bands: Dict[RGB, str],
                       preview_path: str, time_slice=None,
                       size: list[int] = [256, 256]):
    """
    Create a 256x256 preview of datacube and convert it to base64
    """
    if time_slice is None:
        time_slice = dataset.get("t").values[-1]

    # Factor to resize the image
    xfactor = len(dataset.x) // size[0]
    yfactor = len(dataset.y) // size[1]

    overview_data = xr.Dataset()
    for color, band in bands.items():
        overview_data[color.value] = __resize_band(
            dataset, band, xfactor, yfactor, time_slice)

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


def create_preview_b64_cmap(dataset: xr.Dataset, preview: Dict[str, str],
                            preview_path: str, time_slice=None,
                            size: list[int] = [256, 256]):
    if time_slice is None:
        time_slice = dataset.get("t").values[-1]
    cmap, band = list(preview.items())[0]

    # Factor to resize the image
    x_factor = len(dataset.x) // size[0]
    y_factor = len(dataset.y) // size[1]

    data = __resize_band(dataset, band,
                         x_factor, y_factor, time_slice).values

    xlen = data.shape[0]
    ylen = data.shape[1]
    data = data[int((xlen-size[1])/2):int((xlen+size[1])/2),
                int((ylen-size[0])/2):int((ylen+size[0])/2)]

    img = Image.fromarray(cm.get_cmap(cmap)(data, bytes=True))
    img.save(preview_path)

    # encode in base64
    with open(preview_path, 'rb') as fb:
        b64_image = base64.b64encode(fb.read()).decode('utf-8')

    return b64_image


def add_text_on_white_band(imgPath: str, text: str):
    img = Image.open(imgPath)
    band_height = img.height // 10

    font = ImageFont.truetype(FONT, int(band_height * 0.6))

    # Add white band to the preview
    img_band = Image.new("RGB", (img.width, img.height + band_height), "White")
    img_band.paste(img)

    # Create an editable object of the image
    img_edit = ImageDraw.Draw(img_band)

    # Add centered text in the white band
    text_pos = ((img.width - font.getsize(text)[0]) / 2,
                img.height + (band_height - font.getsize(text)[1]) / 2)
    img_edit.text(text_pos, text, (0, 0, 0), font=font)

    img_band.save(imgPath)
