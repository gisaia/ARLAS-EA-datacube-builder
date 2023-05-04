import os
from pathlib import Path

import yaml

ROOT_PATH = Path(__file__).parent.parent.parent


class ServerConfiguration:
    conf_file = str(ROOT_PATH.joinpath("configs/app.conf.yml"))
    docker_conf_file = str(ROOT_PATH.joinpath("configs/docker.app.conf.yml"))

    @classmethod
    def set_conf_file(cls, conf_file: str):
        cls.conf_file = conf_file

    @classmethod
    def get_conf_file(cls) -> str:
        return cls.conf_file

    @classmethod
    def get_server_conf(cls) -> dict:
        conf_file = cls.conf_file
        if "IS_DOCKER_LAUNCH" in os.environ and os.environ["IS_DOCKER_LAUNCH"]:
            conf_file = cls.docker_conf_file

        with open(conf_file, 'r') as f:
            try:
                return yaml.safe_load(f)
            except yaml.YAMLError as e:
                print("Error when loading the server configuration:")
                print(e)

    @classmethod
    def get_server_root(cls) -> str:
        conf: dict = cls.get_server_conf()["dc3-builder"]

        return f"http://{conf['host']}:{conf['port']}"
