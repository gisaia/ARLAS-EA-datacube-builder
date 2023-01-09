#!/usr/bin/python3

import argparse
import xarray as xr
import re
import os
import shutil

import sys
from pathlib import Path
ROOT_PATH = str(Path(__file__).parent.parent)
sys.path.insert(0, ROOT_PATH)
from utils.preview import createPreviewB64


def create_gif(datacube: xr.Dataset, asset: str, gif_name: str):
    # Find where to put the temporary pictures
    matches = re.findall(r"(.*)\.gif", gif_name)
    if len(matches) == 0:
        gifRootPath = gif_name
    else:
        gifRootPath = matches[0]
    os.makedirs(f"tmp/{gifRootPath}", exist_ok=True)

    # Generate the pictures for the gif
    for t in datacube.t.values:
        createPreviewB64(datacube, asset, f"tmp/{gifRootPath}/{t}.jpg", t)

    # Create the gif and clean-up
    os.system(f"cd tmp/{gifRootPath};" +
              f"convert -delay 100 -loop 0 *.jpg {ROOT_PATH}/{gif_name};")
    shutil.rmtree(f"tmp/{gifRootPath}")


if __name__ == "__main__":
    """
    Creates a gif of all the time slices of the given asset of the datacube.
    If no path is given for the gif, then it is given the same as the datacube,
     with an added gif extension.
    """

    parser = argparse.ArgumentParser(
        description="Script to build gifs from datacubes")
    parser.add_argument("--datacubePath", dest="datacubePath",
                        help="Path to the datacube")
    parser.add_argument("--asset", dest="asset",
                        help="The asset to generate a gif of")
    parser.add_argument("--gifPath", dest="gifPath",
                        help="Path to the output gif")

    args = parser.parse_args()

    error = False
    if args.datacubePath is None:
        print("[ERROR] A datacube is needed")
        error = True
    if args.asset is None:
        print("[ERROR] An asset is needed")
        error = True
    if error:
        exit

    gifPath = args.gifPath
    if gifPath is None:
        gifPath = f"{args.datacubePath}.gif"

    datacube = xr.open_zarr(args.datacubePath)
    create_gif(datacube, args.asset, gifPath)
    print(f"[SUCCESS] Created the gif {gifPath}")
