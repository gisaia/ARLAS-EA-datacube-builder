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
from PIL import Image, ImageDraw, ImageFont

ROOT_PATH = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, ROOT_PATH)
from datacube.core.models.enums import RGB
from datacube.core.visualisation.preview import (create_preview_b64,
                                                 create_preview_b64_cmap)

TMP_DIR = "tmp/"
MAX_GIF_SIZE = 10000
FONT = "./assets/Roboto-Light.ttf"
FONT_ITALIC = "./assets/Roboto-LightItalic.ttf"
TEXT_COLOR = (0, 0, 0)


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


def add_text_on_image(imgPath: str, name: str,
                      description: str, bottom_text: str):
    img = Image.open(imgPath)
    band_height = img.height // 10
    description_band_height = img.height // 20

    font = ImageFont.truetype(FONT, int(band_height * 0.6))
    # TODO: change font based on description length and/or split text
    small_font = ImageFont.truetype(FONT_ITALIC, int(band_height * 0.6 * 0.6))

    # Add white bands to the preview
    # Top band + bottom band + description band
    img_total_height = img.height + 2 * band_height + description_band_height
    img_band = Image.new("RGB", (img.width, img_total_height), "White")
    img_band.paste(img, (0, band_height + description_band_height))

    # Create an editable object of the image
    img_edit = ImageDraw.Draw(img_band)

    # Add centered text in the top white band
    name_pos = ((img.width - font.getsize(name)[0]) / 2,
                (band_height - font.getsize(name)[1]) / 2)
    description_pos = ((img.width - small_font.getsize(description)[0]) / 2,
                       band_height + (description_band_height -
                                      small_font.getsize(description)[1]) / 2)
    img_edit.text(name_pos, name, TEXT_COLOR, font=font)
    img_edit.text(description_pos, description, TEXT_COLOR, font=small_font)

    # Add centered text in the bottom white band
    bottom_text_pos = ((img.width - font.getsize(bottom_text)[0]) / 2,
                       img_total_height - band_height + (
                            band_height - font.getsize(bottom_text)[1]) / 2)
    img_edit.text(bottom_text_pos, bottom_text, TEXT_COLOR, font=font)

    # Add the credits
    credits = "Powered by ARLAS (Gisaïa)"
    credits_pos = (img.width - small_font.getsize(credits)[0],
                   img_total_height - small_font.getsize(credits)[1])
    img_edit.text(credits_pos, credits, TEXT_COLOR, font=small_font)

    img_band.save(imgPath)


def create_gif(datacube: xr.Dataset, dc_name: str, dc_description: str,
               gif_name: str, size: list[int]):
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
        if len(datacube.attrs["dc3:preview"]) == 3:
            rgb = {RGB.RED: datacube.attrs["dc3:preview"]["RED"],
                   RGB.GREEN: datacube.attrs["dc3:preview"]["GREEN"],
                   RGB.BLUE: datacube.attrs["dc3:preview"]["BLUE"]}
            create_preview_b64(datacube, rgb, img_path, t, size=size)
        else:
            create_preview_b64_cmap(datacube, datacube.attrs["dc3:preview"],
                                    img_path, t, size=size)
        add_text_on_image(img_path, dc_name, dc_description, t_text)

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
    parser.add_argument("-n", dest="name",
                        help="Name of the datacube to display on the gif")
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
    datacube_name = args.name if args.name \
        else args.datacube_path.split("/")[-1]
    datacube_description = datacube.attrs["dc3:description"]

    if args.big:
        size = [len(datacube.x), len(datacube.y)]
        while size[0] > MAX_GIF_SIZE or size[1] > MAX_GIF_SIZE:
            size = [size[0] // 4, size[1] // 4]

    create_gif(datacube, datacube_name, datacube_description, gif_path, size)
    print(f"[SUCCESS] Created the gif {gif_path}")
