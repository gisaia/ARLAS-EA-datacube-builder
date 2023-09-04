import os
import os.path as path
import re
import shutil
from datetime import datetime
from pathlib import Path

import xarray as xr
from PIL import Image, ImageDraw, ImageFont

from datacube.core.logging.logger import CustomLogger as Logger
from datacube.core.models.enums import RGB
from datacube.core.visualisation.preview import (create_preview_b64,
                                                 create_preview_b64_cmap,
                                                 prepare_visualisation)

ROOT_PATH = str(Path(__file__).parent.parent.parent.parent)
MAX_GIF_SIZE = 2048
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
    description_band_height = (1 if description else 0) * img.height // 20

    font = ImageFont.truetype(FONT, int(band_height * 0.6))
    # TODO: change font based on description length and/or split text
    small_font = ImageFont.truetype(FONT_ITALIC, int(band_height * 0.6 * 0.3))

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
    img_edit.text(name_pos, name, TEXT_COLOR, font=font)

    if description:
        text_size = small_font.getsize(description)
        description_pos = ((img.width - text_size[0]) / 2,
                           band_height + (description_band_height -
                                          text_size[1]) / 2)
        img_edit.text(description_pos, description,
                      TEXT_COLOR, font=small_font)

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


def create_gif(datacube: xr.Dataset, dc_name: str,
               gif_name: str, size: [int, int],
               relative_output_dir="output", relative_tmp_dir="tmp"):
    """
    Create a gif based on a datacube
    """
    Logger.get_logger().info("Generating gif")
    # Find where to put the temporary pictures
    matches = re.findall(r"(.*)\.(?i)gif", gif_name)
    if len(matches) == 0:
        gif_root_path = gif_name
    else:
        gif_root_path = matches[0]
    os.makedirs(path.join(relative_tmp_dir, gif_root_path), exist_ok=True)

    times = list(map(lambda t: datetime.fromtimestamp(t), datacube.t.values))

    # Normalize all slices the same way to have more meaningful gifs
    coarsed_datacube, clip_values = prepare_visualisation(
        datacube, list(datacube.attrs["dc3:preview"].values()), size)

    # Generate the pictures for the gif
    for t_text, t in zip(truncate_datetime(times), datacube.t.values):
        img_path = path.join(relative_tmp_dir, gif_root_path, f"{t}.png")
        if len(datacube.attrs["dc3:preview"]) == 3:
            rgb = {RGB.RED: datacube.attrs["dc3:preview"]["RED"],
                   RGB.GREEN: datacube.attrs["dc3:preview"]["GREEN"],
                   RGB.BLUE: datacube.attrs["dc3:preview"]["BLUE"]}
            create_preview_b64(coarsed_datacube,
                               rgb,
                               img_path, clip_values,
                               time_slice=t, size=size)
        else:
            create_preview_b64_cmap(coarsed_datacube,
                                    datacube.attrs["dc3:preview"],
                                    img_path, clip_values,
                                    time_slice=t, size=size)
        add_text_on_image(img_path, dc_name,
                          datacube.attrs.get("description"), t_text)

    # Create the gif and clean-up
    os.system(f"cd {path.join(relative_tmp_dir, gif_root_path)};" +
              "convert -delay 100 -loop 0 *.png " +
              path.join(ROOT_PATH, relative_output_dir, gif_name))
    shutil.rmtree(f"{path.join(relative_tmp_dir, gif_root_path)}")

    Logger.get_logger().info("Gif generated")


def get_gif_size(datacube: xr.Dataset,
                 max_gif_size=MAX_GIF_SIZE) -> [int, int]:
    """
    Returns the [length, width] in pixels of the gif to generate
    """
    if len(datacube.x) <= max_gif_size and len(datacube.y) <= max_gif_size:
        return [len(datacube.x), len(datacube.y)]
    else:
        if len(datacube.x) <= len(datacube.y):
            return [max_gif_size,
                    int(len(datacube.y) * max_gif_size / len(datacube.x))]
        return [int(len(datacube.x) * max_gif_size / len(datacube.y)),
                max_gif_size]
