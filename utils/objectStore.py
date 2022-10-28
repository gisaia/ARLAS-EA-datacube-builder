from urllib.parse import urlparse
from models.objectStoreDrivers.gcsObjectStore import GCSObjectStore
from models.objectStoreDrivers.abstractObjectStore import AbstractObjectStore

from pathlib import Path
from envyaml import EnvYAML
from fsspec import get_mapper, FSMap

ROOT_PATH = str(Path(__file__).parent.parent)
INPUT_OBJECT_STORE = EnvYAML(ROOT_PATH + "/configs/inputObjectStore.yml")
OUTPUT_OBJECT_STORE = EnvYAML(ROOT_PATH + "/configs/outputObjectStore.yml")


def createInputObjectStore(objStoreType) -> AbstractObjectStore:
    if objStoreType == "gs":
        return GCSObjectStore(
            INPUT_OBJECT_STORE["gs.api_key"])
    else:
        raise NotImplementedError(
            f"Object store {objStoreType} not implemented")


def getMapperOutputObjectStore(destination) -> FSMap:
    destinationParsed = urlparse(destination)
    return get_mapper(
        destination, mode="w",
        token=OUTPUT_OBJECT_STORE[f"{destinationParsed.scheme}.api_key"])