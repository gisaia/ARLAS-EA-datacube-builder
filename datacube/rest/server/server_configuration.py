from pathlib import Path

import yaml

from datacube.core.logging.logger import CustomLogger as Logger
from datacube.rest.server.models.server_configuration import \
    ServerConfigurationModel

ROOT_PATH = Path(__file__).parent.parent.parent.parent
LOGGER = Logger.get_logger()


class ServerConfiguration:
    conf_file = str(ROOT_PATH.joinpath("configs/app.conf.yml"))

    @classmethod
    def set_conf_file(cls, conf_file: str):
        cls.conf_file = conf_file

    @classmethod
    def get_conf_file(cls) -> str:
        return cls.conf_file

    @classmethod
    def get_server_conf(cls) -> ServerConfigurationModel:
        with open(cls.conf_file, 'r') as f:
            try:
                return ServerConfigurationModel(**yaml.safe_load(f))
            except yaml.YAMLError as e:
                LOGGER.error("Error when loading the server configuration:")
                LOGGER.error(e)

    @classmethod
    def get_server_root(cls) -> str:
        conf = cls.get_server_conf().dc3_builder

        return f"http://{conf.host}:{conf.port}"

    @classmethod
    def is_pivot_format(cls) -> bool:
        pivot_format = cls.get_server_conf().dc3_builder.pivot_format
        return pivot_format is not None and pivot_format
