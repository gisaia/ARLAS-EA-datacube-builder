from .abstractObjectStore import AbstractObjectStore
from google.cloud.storage import Client
from google.oauth2 import service_account


class GCSObjectStore(AbstractObjectStore):

    def __init__(self, api_key):
        credentials = service_account.Credentials.from_service_account_info(
            api_key)
        self.client = Client("DataCubeBuilder", credentials=credentials)
