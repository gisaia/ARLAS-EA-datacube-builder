#!/usr/bin/python3

import argparse

import sys
from pathlib import Path

import xarray as xr

from datacube.core.visualisation.gif import create_gif, get_gif_size


ROOT_PATH = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, ROOT_PATH)


TMP_DIR = "tmp/"
MAX_GIF_SIZE = 10000


if __name__ == "__main__":
    """
    Creates a gif of all the time slices of the given band of the datacube.
    If no path is given for the gif, then it is given the same as the datacube,
     with an added gif extension.
    """

    parser = argparse.ArgumentParser(
        description="Script to build gifs from datacubes")
    parser.add_argument("-d", dest="datacube_path",
                        help="Path to the datacube")
    parser.add_argument("-n", dest="name",
                        help="Name of the datacube to display on the gif")
    parser.add_argument("-s", dest="size", nargs='+', type=int,
                        help="Size of the gif")
    parser.add_argument("--big", dest="big", action="store_true")

    args = parser.parse_args()

    if args.datacube_path is None:
        print("[ERROR] A datacube is needed")
        exit

    size = args.size if args.size and len(args.size) == 2 else [256, 256]

    datacube = xr.open_zarr(args.datacube_path)
    # Either use the name given in command line,
    # or take the datacube name extracted from its path, minus any trailing "/"
    datacube_name = args.name if args.name \
        else (args.datacube_path[:-1] if args.datacube_path[-1] == "/"
              else args.datacube_path).split("/")[-1]
    datacube_description = datacube.attrs.get("description")

    gif_name = f"{datacube_name}.gif"

    if args.big:
        size = get_gif_size(datacube)

    create_gif(datacube, datacube_name, gif_name, size)
    print(f"[SUCCESS] Created the gif {gif_name}")
