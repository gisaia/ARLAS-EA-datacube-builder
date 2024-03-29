from google.cloud.storage import Client
from google.oauth2 import service_account

from datacube.core.storage.drivers.abstract import AbstractStorage


class GCStorage(AbstractStorage):

    def __init__(self, api_key):
        credentials = service_account.Credentials.from_service_account_info(
            api_key)
        self.client = Client("DataCubeBuilder", credentials=credentials)
