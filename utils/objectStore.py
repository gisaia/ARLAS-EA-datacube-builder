from models.objectStoreDrivers.gcsObjectStore import GCSObjectStore
from models.objectStoreDrivers.abstractObjectStore import AbstractObjectStore

from pathlib import Path
from envyaml import EnvYAML

ROOT_PATH = str(Path(__file__).parent.parent)
INPUT_OBJECT_STORE_CONF = EnvYAML(ROOT_PATH + "/configs/inputObjectStore.yml")


def createInputObjectStore(objStoreType) -> AbstractObjectStore:
    if objStoreType == "gs":
        return GCSObjectStore(
            INPUT_OBJECT_STORE_CONF["gs.api_key"])
    else:
        raise NotImplementedError(
            f"Object store {objStoreType} not implemented")
