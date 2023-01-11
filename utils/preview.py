import xarray as xr
import base64
# Apparently necessary for the .rio to work
import rioxarray


def _bandTo256(dataset: xr.Dataset, asset: str, xfactor, yfactor):
    """
    Put a band values between 0 and 255
    """
    band: xr.DataArray = dataset[asset].isel(t=-1)
    min = band.min()
    max = band.max()

    """ Change the resolution """
    band = band.coarsen({"x": xfactor, "y": yfactor}, boundary="pad").mean()

    """ Normalize values within [0-255] """
    band = ((band - min) * 255.0 / (max - min)).astype('uint8')
    return band.transpose().reindex(y=band.y[::-1])


def createPreviewB64(dataset: xr.Dataset, asset: str, overviewPath: str):
    """
    Create a 256x256 preview of datacube and convert it to base64
    """
    # We want a 256x256 pic
    xfactor = len(dataset.x) // 256
    yfactor = len(dataset.y) // 256
    overview_data = xr.Dataset({
        "grey": _bandTo256(dataset, asset, xfactor, yfactor)
    })

    # Cut the x and y to have 256x256
    xlen = len(overview_data.x)
    ylen = len(overview_data.y)
    overview_data = overview_data.isel(
        x=slice(int((xlen-256)/2), int((xlen+256)/2)),
        y=slice(int((ylen-256)/2), int((ylen+256)/2)))

    overview_data.rio.to_raster(
        "{}".format(overviewPath),
        driver="PNG"
    )

    # encode en base64
    binaryFileContent = open(overviewPath, 'rb').read()
    base64Image = base64.b64encode(binaryFileContent).decode('utf-8')

    return base64Image
