from typing import Tuple
from models.objectStoreDrivers.gcsObjectStore import GCSObjectStore
from models.objectStoreDrivers.abstractObjectStore import AbstractObjectStore

from pathlib import Path
from envyaml import EnvYAML
from fsspec import get_mapper, FSMap
from os.path import join

ROOT_PATH = str(Path(__file__).parent.parent)
INPUT_OBJECT_STORE = EnvYAML(join(ROOT_PATH, "configs/inputObjectStore.yml"))
OUTPUT_OBJECT_STORE = EnvYAML(join(ROOT_PATH, "configs/outputObjectStore.yml"))


def createInputObjectStore(objStoreType) -> AbstractObjectStore:
    if objStoreType == "gs":
        return GCSObjectStore(
            INPUT_OBJECT_STORE["gs.api_key"])
    else:
        raise NotImplementedError(
            f"Object store {objStoreType} not implemented")


# By default uses GCS as an object store
def createOutputObjectStore() -> AbstractObjectStore:
    return GCSObjectStore(
        OUTPUT_OBJECT_STORE["gs.api_key"])


# By default uses GCS as an object store
def getMapperOutputObjectStore(destination) -> Tuple[str, FSMap]:
    url = f"gs://{OUTPUT_OBJECT_STORE['gs.bucket']}/{destination}"
    return url, get_mapper(url, mode="w",
                           token=OUTPUT_OBJECT_STORE["gs.api_key"])
