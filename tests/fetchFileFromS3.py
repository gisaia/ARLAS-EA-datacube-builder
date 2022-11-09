#!/usr/bin/python3

import sys
from pathlib import Path
import zipfile
import smart_open as so
from envyaml import EnvYAML

ROOT_PATH = str(Path(__file__).parent.parent)
sys.path.insert(0, ROOT_PATH)
from models.objectStoreDrivers.gcsObjectStore import GCSObjectStore

config = EnvYAML(ROOT_PATH + "/configs/inputObjectStore.yml")
rasterURI = "gs://gisaia-arlasea/S2A_MSIL2A_20220904T103641_N0400_R008_T33WVN_20220904T160606"

objectStore = GCSObjectStore(config["gs.api_key"])
params = {'client': objectStore.client}

with so.open(rasterURI, "rb", transport_params=params) as fileBytes:
    with zipfile.ZipFile(fileBytes) as zip:
        print(zip.filelist)
