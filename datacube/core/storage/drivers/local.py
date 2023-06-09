from datacube.core.storage.drivers.abstract import AbstractStorage


class LocalStorage(AbstractStorage):

    def __init__(self):
        self.client = None
