#!/usr/bin/python3

import sys
from pathlib import Path
import xarray as xr
from envyaml import EnvYAML

ROOT_PATH = str(Path(__file__).parent.parent)
sys.path.insert(0, ROOT_PATH)

from utils.objectStore import getMapperOutputObjectStore

INPUT_FILE = "output/zarr/post"
DEST = "gs://gisaia-datacube/test"

OBJECT_STORE_CONF = EnvYAML(ROOT_PATH + "/configs/outputObjectStore.yml")

ds = xr.open_zarr(INPUT_FILE)
mapper = getMapperOutputObjectStore(DEST)
print(ds.to_zarr(mapper))
