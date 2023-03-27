from typing import Tuple
from pathlib import Path
from envyaml import EnvYAML
from fsspec import get_mapper, FSMap
from os.path import join

from datacube.core.object_store.drivers.gcs import GCSObjectStore
from datacube.core.object_store.drivers.abstract import AbstractObjectStore

ROOT_PATH = str(Path(__file__).parent.parent.parent.parent)
INPUT_OBJECT_STORE = EnvYAML(join(ROOT_PATH, "configs/inputObjectStore.yml"))
OUTPUT_OBJECT_STORE = EnvYAML(join(ROOT_PATH, "configs/outputObjectStore.yml"))


def create_input_object_store(obj_store_type) -> AbstractObjectStore:
    if obj_store_type == "gs":
        return GCSObjectStore(
            INPUT_OBJECT_STORE["gs.api_key"])
    else:
        raise NotImplementedError(
            f"Object store {obj_store_type} not implemented")


# By default uses GCS as an object store
def create_output_object_store() -> AbstractObjectStore:
    return GCSObjectStore(
        OUTPUT_OBJECT_STORE["gs.api_key"])


# By default uses GCS as an object store
def get_mapper_output_object_store(destination) -> Tuple[str, FSMap]:
    url = f"gs://{OUTPUT_OBJECT_STORE['gs.bucket']}/{destination}"
    return url, get_mapper(url, mode="w",
                           token=OUTPUT_OBJECT_STORE["gs.api_key"])
