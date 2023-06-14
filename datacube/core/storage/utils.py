from os.path import join
from pathlib import Path

import smart_open as so
from envyaml import EnvYAML
from fsspec import FSMap, get_mapper

from datacube.core.storage.drivers.abstract import AbstractStorage
from datacube.core.storage.drivers.gcs import GCStorage
from datacube.core.storage.drivers.local import LocalStorage

ROOT_PATH = str(Path(__file__).parent.parent.parent.parent)
INPUT_STORAGE = EnvYAML(join(ROOT_PATH, "configs/app.conf.yml"))["input"]
OUTPUT_STORAGE = EnvYAML(join(ROOT_PATH, "configs/app.conf.yml"))["output"]


def create_input_storage(storage_type) -> AbstractStorage:
    if not storage_type:
        return LocalStorage()
    if storage_type == "gs":
        return GCStorage(INPUT_STORAGE["gs"]["api_key"])
    else:
        raise NotImplementedError(
            f"Storage '{storage_type}' not implemented")


def get_local_root_directory() -> str:
    return INPUT_STORAGE["local"]["root_directory"]


def get_full_adress(destination) -> str:
    if is_output_storage_local():
        return join(OUTPUT_STORAGE["local"]["directory"], destination)
    elif is_output_storage_gs():
        return f"gs://{OUTPUT_STORAGE['gs']['bucket']}/{destination}"


def get_mapper_output(destination) -> tuple[str, FSMap] | tuple[str, str]:
    """
    Returns the adress (local or object store) at which the desired file
    will be uploaded, as well as the mapping to write it.
    In the case of local storage, the mapping is the adress.
    """
    if is_output_storage_local():
        path = get_full_adress(destination)
        return path, path
    elif is_output_storage_gs():
        url = get_full_adress(destination)
        return url, get_mapper(url, mode="w",
                               token=OUTPUT_STORAGE["gs"]["api_key"])


def write_bytes(destination: str, data: bytes) -> str:
    """
    Writes bytes data to the configured storage, and returns its location.
    """
    path = get_full_adress(destination)
    if is_output_storage_local():
        client = None
    elif is_output_storage_gs():
        client = GCStorage(OUTPUT_STORAGE["gs"]["api_key"]).client
    else:
        raise NotImplementedError(
            f"Output storage {OUTPUT_STORAGE['storage']} not implemented")

    with so.open(path, "wb", transport_params={"client": client}) as fb:
        fb.write(data)
        return path


def is_output_storage_local() -> bool:
    return OUTPUT_STORAGE["storage"] == "local"


def is_output_storage_gs() -> bool:
    return OUTPUT_STORAGE["storage"] == "gs"
