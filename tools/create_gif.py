#!/usr/bin/python3

import argparse
import xarray as xr
import re
import os
import shutil
from typing import Dict

import sys
from pathlib import Path
ROOT_PATH = str(Path(__file__).parent.parent)
sys.path.insert(0, ROOT_PATH)
from utils.preview import createPreviewB64


def create_gif(datacube: xr.Dataset, rgb: Dict[str, str], gif_name: str):
    # Find where to put the temporary pictures
    matches = re.findall(r"(.*)\.gif", gif_name)
    if len(matches) == 0:
        gifRootPath = gif_name
    else:
        gifRootPath = matches[0]
    os.makedirs(f"tmp/{gifRootPath}", exist_ok=True)

    # Generate the pictures for the gif
    for t in datacube.t.values:
        createPreviewB64(datacube, rgb, f"tmp/{gifRootPath}/{t}.jpg", t)

    # Create the gif and clean-up
    os.system(f"cd tmp/{gifRootPath};" +
              f"convert -delay 100 -loop 0 *.jpg {ROOT_PATH}/{gif_name}")
    shutil.rmtree(f"tmp/{gifRootPath}")


if __name__ == "__main__":
    """
    Creates a gif of all the time slices of the given asset of the datacube.
    If no path is given for the gif, then it is given the same as the datacube,
     with an added gif extension.
    """

    parser = argparse.ArgumentParser(
        description="Script to build gifs from datacubes")
    parser.add_argument("-d", "--datacubePath", dest="datacubePath",
                        help="Path to the datacube")
    parser.add_argument("--rgb", dest="rgb", nargs="+",
                        help="The bands to use for an RGB picture." +
                             "If one is given, generates a grey one")
    parser.add_argument("-g", "--gifPath", dest="gifPath",
                        help="Path to the output gif")

    args = parser.parse_args()

    error = False
    if args.datacubePath is None:
        print("[ERROR] A datacube is needed")
        error = True
    if args.rgb is None:
        print("[ERROR] Bands are needed")
        error = True
    if error:
        exit

    gifPath = args.gifPath
    if gifPath is None:
        gifPath = f"{args.datacubePath}.gif"

    datacube = xr.open_zarr(args.datacubePath)

    # Attribute the RGB bands to the input assets
    if len(args.rgb) == 1:
        rgb = {"R": args.rgb[0], "G": args.rgb[0], "B": args.rgb[0]}
    elif len(args.rgb) == 2:
        raise ValueError("There must be 1 or 3 assets, not 2")
    elif len(args.rgb) == 3:
        rgb = {"R": args.rgb[0], "G": args.rgb[1], "B": args.rgb[2]}
    else:
        raise ValueError(f"There must be 1 or 3 assets, not {len(args.rgb)}")
    create_gif(datacube, rgb, gifPath)
    print(f"[SUCCESS] Created the gif {gifPath}")
