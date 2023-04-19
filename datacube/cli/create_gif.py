#!/usr/bin/python3

import argparse
import os
import os.path as path
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import xarray as xr

ROOT_PATH = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, ROOT_PATH)
from datacube.core.models.enums import RGB
from datacube.core.visualisation.preview import (add_text_on_white_band,
                                                 create_preview_b64,
                                                 create_preview_b64_cmap)

TMP_DIR = "tmp/"
MAX_GIF_SIZE = 10000


def truncate_datetime(times: list[datetime]) -> list[str]:
    """
    Finds the biggest common denominator of a list of times
    to get the shortest common representation
    """
    if any(t.second != times[0].second for t in times):
        return map(lambda t: t.__str__(), times)
    if any(t.minute != times[0].minute for t in times):
        return map(lambda t: t.__str__()[:-3], times)
    # Better to display minutes with hours
    if any(t.hour != times[0].hour for t in times):
        return map(lambda t: t.__str__()[:-3], times)
    if any(t.day != times[0].day for t in times):
        return map(lambda t: t.__str__()[:-9], times)
    if any(t.month != times[0].month for t in times):
        return map(lambda t: t.__str__()[:-12], times)
    return map(lambda t: str(t.year), times)


def create_gif(datacube: xr.Dataset, gif_name: str, size: list[int]):
    # Find where to put the temporary pictures
    matches = re.findall(r"(.*)\.gif", gif_name)
    if len(matches) == 0:
        gif_root_path = gif_name
    else:
        gif_root_path = matches[0]
    os.makedirs(path.join(TMP_DIR, gif_root_path), exist_ok=True)

    times = list(map(lambda t: datetime.fromtimestamp(t), datacube.t.values))

    # Generate the pictures for the gif
    for t_text, t in zip(truncate_datetime(times), datacube.t.values):
        img_path = path.join(TMP_DIR, gif_root_path, f"{t}.png")
        if len(datacube.attrs["preview"]) == 3:
            rgb = {RGB.RED: datacube.attrs["preview"]["RED"],
                   RGB.GREEN: datacube.attrs["preview"]["GREEN"],
                   RGB.BLUE: datacube.attrs["preview"]["BLUE"]}
            create_preview_b64(datacube, rgb, img_path, t, size=size)
        else:
            create_preview_b64_cmap(datacube, datacube.attrs["preview"],
                                    img_path, t, size=size)
        add_text_on_white_band(img_path, t_text)

    # Create the gif and clean-up
    os.system(f"cd {path.join(TMP_DIR, gif_root_path)};" +
              "convert -delay 100 -loop 0 *.png " +
              path.join(ROOT_PATH, gif_name))
    shutil.rmtree(f"{path.join(TMP_DIR, gif_root_path)}")


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
    parser.add_argument("-s", dest="size", nargs='+', type=int,
                        help="Size of the gif")
    parser.add_argument("--big", dest="big", action="store_true")

    args = parser.parse_args()

    if args.datacube_path is None:
        print("[ERROR] A datacube is needed")
        exit

    gif_path = f"{args.datacube_path.rstrip('/')}.gif"
    size = args.size if args.size and len(args.size) == 2 else [256, 256]

    datacube = xr.open_zarr(args.datacube_path)

    if args.big:
        size = [len(datacube.x), len(datacube.y)]
        while size[0] > MAX_GIF_SIZE or size[1] > MAX_GIF_SIZE:
            size = [size[0] // 4, size[1] // 4]

    create_gif(datacube, gif_path, size)
    print(f"[SUCCESS] Created the gif {gif_path}")
