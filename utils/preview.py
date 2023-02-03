import xarray as xr
import base64
# Apparently necessary for the .rio to work
import rioxarray
from typing import Dict

from PIL import Image
from matplotlib import cm

from utils.enums import RGB


def _bandTo256(dataset: xr.Dataset, band: str, xfactor, yfactor, timeSlice):
    """
    Put a band values between 0 and 255
    """
    band: xr.DataArray = dataset[band].sel(t=timeSlice)

    """ Change the resolution """
    band = band.coarsen({"x": xfactor, "y": yfactor}, boundary="pad").mean()

    """ Clip the 2% of highest and lowest values """
    min, max = band.chunk({"x": -1, "y": -1}) \
                   .quantile([0.02, 0.98], dim=["x", "y"]).values
    band = xr.where(band > max, max, band)
    band = xr.where(band < min, min, band)

    """ Normalize values within [0-255] """
    band = ((band - min) * 255.0 / (max - min)).astype('uint8')
    return band.transpose().reindex(y=band.y[::-1])


def createPreviewB64(dataset: xr.Dataset, bands: Dict[RGB, str],
                     previewPath: str, timeSlice=None):
    """
    Create a 256x256 preview of datacube and convert it to base64
    """
    if timeSlice is None:
        timeSlice = dataset.t.values[-1]
    # We want a 256x256 pic
    xfactor = len(dataset.x) // 256
    yfactor = len(dataset.y) // 256

    overview_data = xr.Dataset()
    for color, band in bands.items():
        overview_data[color.value] = _bandTo256(
            dataset, band, xfactor, yfactor, timeSlice)

    # Cut the x and y to have 256x256
    xlen = len(overview_data.x)
    ylen = len(overview_data.y)
    overview_data = overview_data.isel(
        x=slice(int((xlen-256)/2), int((xlen+256)/2)),
        y=slice(int((ylen-256)/2), int((ylen+256)/2)))

    overview_data.rio.to_raster(f"{previewPath}", driver="PNG")
    overview_data.close()
    del overview_data

    # encode in base64
    with open(previewPath, 'rb') as fb:
        base64Image = base64.b64encode(fb.read()).decode('utf-8')

    return base64Image


def createPreviewB64Cmap(dataset: xr.Dataset, band: str,
                         previewPath: str, cmap: str = "rainbow",
                         timeSlice=None):
    if timeSlice is None:
        timeSlice = dataset.t.values[-1]
    # We want a 256x256 pic
    xfactor = len(dataset.x) // 256
    yfactor = len(dataset.y) // 256

    data = _bandTo256(dataset, band, xfactor, yfactor, timeSlice).values

    # Cut the x and y to have 256x256
    xlen = data.shape[0]
    ylen = data.shape[0]
    data = data[int((xlen-256)/2):int((xlen+256)/2), int((ylen-256)/2):int((ylen+256)/2)]

    img = Image.fromarray(cm.get_cmap(cmap)(data, bytes=True))
    img.save(previewPath)

    # encode in base64
    with open(previewPath, 'rb') as fb:
        base64Image = base64.b64encode(fb.read()).decode('utf-8')

    return base64Image
