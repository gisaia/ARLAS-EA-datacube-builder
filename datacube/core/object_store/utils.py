from os.path import join
from pathlib import Path

import smart_open as so
from envyaml import EnvYAML
from fsspec import FSMap, get_mapper

from datacube.core.object_store.drivers.abstract import AbstractObjectStore
from datacube.core.object_store.drivers.gcs import GCSObjectStore

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


def get_full_adress(destination) -> str:
    if is_output_storage_local():
        return join(OUTPUT_OBJECT_STORE["directory"], destination)
    elif is_output_storage_gs():
        return f"gs://{OUTPUT_OBJECT_STORE['bucket']}/{destination}"


def get_mapper_output(
        destination) -> tuple[str, FSMap]:
    """
    Returns the adress (local or object store) at which the desired file
    will be uploaded, as well as the mapping to write it.
    """
    if is_output_storage_local():
        path = get_full_adress(destination)
        return path, path
    elif is_output_storage_gs():
        url = get_full_adress(destination)
        return url, get_mapper(url, mode="w",
                               token=OUTPUT_OBJECT_STORE["api_key"])


def write_bytes(destination: str, data: bytes) -> str:
    """
    Writes bytes data to the configured storage, and returns its location.
    """
    if is_output_storage_local():
        path = get_full_adress(destination)
        with open(path, "wb") as f:
            f.write(data)
        return path
    elif is_output_storage_gs():
        url = get_full_adress(destination)
        client = GCSObjectStore(OUTPUT_OBJECT_STORE["api_key"]).client
        with so.open(url, "wb", transport_params={"client": client}) as fb:
            fb.write(data)
        return url


def is_output_storage_local() -> bool:
    return OUTPUT_OBJECT_STORE["storage"] == "local"


def is_output_storage_gs() -> bool:
    return OUTPUT_OBJECT_STORE["storage"] == "gs"
