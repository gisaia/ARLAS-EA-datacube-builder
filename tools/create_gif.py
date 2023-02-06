#!/usr/bin/python3

import argparse
import xarray as xr
import re
import os
import os.path as path
import shutil
from typing import Dict

import sys
from pathlib import Path
ROOT_PATH = str(Path(__file__).parent.parent)
sys.path.insert(0, ROOT_PATH)
from utils.preview import createPreviewB64, createPreviewB64Cmap
from utils.enums import RGB

TMP_DIR = "tmp/"


def create_gif(datacube: xr.Dataset, gif_name: str):
    # Find where to put the temporary pictures
    matches = re.findall(r"(.*)\.gif", gif_name)
    if len(matches) == 0:
        gifRootPath = gif_name
    else:
        gifRootPath = matches[0]
    os.makedirs(path.join(TMP_DIR, gifRootPath), exist_ok=True)

    # Generate the pictures for the gif
    for t in datacube.t.values:
        imgPath = path.join(TMP_DIR, gifRootPath, f"{t}.png")
        if len(datacube.attrs["preview"]) == 3:
            rgb = {RGB.RED: datacube.attrs["preview"]["RED"],
                   RGB.GREEN: datacube.attrs["preview"]["GREEN"],
                   RGB.BLUE: datacube.attrs["preview"]["BLUE"]}
            createPreviewB64(datacube, rgb,
                             imgPath, t)
        else:
            createPreviewB64Cmap(datacube, datacube.attrs["preview"],
                                 imgPath, t)

    # Create the gif and clean-up
    os.system(f"cd {path.join(TMP_DIR, gifRootPath)};" +
              "convert -delay 100 -loop 0 *.png " +
              path.join(ROOT_PATH, gif_name))
    shutil.rmtree(f"{path.join(TMP_DIR, gifRootPath)}")


if __name__ == "__main__":
    """
    Creates a gif of all the time slices of the given band of the datacube.
    If no path is given for the gif, then it is given the same as the datacube,
     with an added gif extension.
    """

    parser = argparse.ArgumentParser(
        description="Script to build gifs from datacubes")
    parser.add_argument("-d", "--datacubePath", dest="datacubePath",
                        help="Path to the datacube")

    args = parser.parse_args()

    if args.datacubePath is None:
        print("[ERROR] A datacube is needed")
        exit

    gifPath = f"{args.datacubePath.rstrip('/')}.gif"

    datacube = xr.open_zarr(args.datacubePath)

    create_gif(datacube, gifPath)
    print(f"[SUCCESS] Created the gif {gifPath}")
