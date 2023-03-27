#!/usr/bin/python3

import argparse
import xarray as xr
import re
import os
import os.path as path
import shutil
from datetime import datetime
from typing import List

import sys
from pathlib import Path
ROOT_PATH = str(Path(__file__).parent.parent)
sys.path.insert(0, ROOT_PATH)
from utils.preview import create_preview_b64, create_preview_b64_cmap, \
                          add_text_on_white_band
from utils.enums import RGB

TMP_DIR = "tmp/"


def truncate_datetime(times: List[datetime]) -> List[str]:
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


def create_gif(datacube: xr.Dataset, gif_name: str):
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
            create_preview_b64(datacube, rgb,
                               img_path, t)
        else:
            create_preview_b64_cmap(datacube, datacube.attrs["preview"],
                                    img_path, t)
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

    args = parser.parse_args()

    if args.datacube_path is None:
        print("[ERROR] A datacube is needed")
        exit

    gif_path = f"{args.datacube_path.rstrip('/')}.gif"

    datacube = xr.open_zarr(args.datacube_path)

    create_gif(datacube, gif_path)
    print(f"[SUCCESS] Created the gif {gif_path}")
