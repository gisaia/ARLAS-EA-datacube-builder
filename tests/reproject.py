#!/usr/bin/python3

import sys
from pathlib import Path
from time import time
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling, transform_bounds
import numpy as np
from rasterio.mask import mask
from shapely.geometry import Polygon

from rasterio.coords import BoundingBox

ROOT_PATH = str(Path(__file__).parent.parent)
sys.path.insert(0, ROOT_PATH)

from utils.geometry import projectPolygon


IN_PATH = "../data/S2A_MSIL2A_20220809T102041_N0400_R065_T32TML_20220809T180703.SAFE/GRANULE/L2A_T32TML_A037242_20220809T102107/IMG_DATA/R10m/T32TML_20220809T102041_B02_10m.jp2"
OUT_PATH = "../data/reproj/test.jp2"

ROI = [8, 40.8, 9, 42]
DIST_CRS = {"init": 'EPSG:4326'}

with rasterio.open(IN_PATH) as src:
    print(src.crs)

    roi_local = transform_bounds(DIST_CRS, src.crs, *ROI)
    bounds = src.bounds
    rasterPolygon = Polygon([
            (bounds.left, bounds.bottom),
            (bounds.right, bounds.bottom),
            (bounds.right, bounds.top),
            (bounds.left, bounds.top),
            (bounds.left, bounds.bottom)])

    polygon = Polygon([
            (roi_local[0], roi_local[1]),
            (roi_local[2], roi_local[1]),
            (roi_local[2], roi_local[3]),
            (roi_local[0], roi_local[3]),
            (roi_local[0], roi_local[1])])

    projectPolygon(polygon, src.crs, 'EPSG:4326')
    intersectionBounds = polygon.intersection(rasterPolygon).bounds
    bounds = BoundingBox(intersectionBounds[0],
                         intersectionBounds[1],
                         intersectionBounds[2],
                         intersectionBounds[3])

    start_time = time()

    rasterData: np.ndarray
    rasterData, _ = mask(src, [polygon], crop=True)

    dst_transform, width, height = calculate_default_transform(
        src.crs, DIST_CRS, rasterData.shape[0], rasterData.shape[1], *bounds)

    print(src.transform)
    print()
    print(dst_transform)
    print(src.width, width)
    print(src.height, height)

    dst = np.zeros((width, height))

    kwargs = src.meta.copy()

    kwargs.update({
            'crs': DIST_CRS,
            'transform': dst_transform,
            'width': width,
            'height': height})

    with rasterio.open(OUT_PATH, 'w', **kwargs) as destination:
        reproject(
            source=rasterio.band(src, 1),
            destination=rasterio.band(destination, 1),
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=dst_transform,
            dst_crs=DIST_CRS,
            resampling=Resampling.nearest
        )

    print(time() - start_time)
    print(dst)
