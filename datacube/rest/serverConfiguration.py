from pathlib import Path

import yaml

ROOT_PATH = Path(__file__).parent.parent.parent


class ServerConfiguration:
    conf_file = str(ROOT_PATH.joinpath("configs/app.conf.yml"))

    @classmethod
    def set_conf_file(cls, conf_file: str):
        cls.conf_file = conf_file

    @classmethod
    def get_conf_file(cls) -> str:
        return cls.conf_file

    @classmethod
    def get_server_conf(cls) -> dict:
        with open(cls.conf_file, 'r') as f:
            try:
                return yaml.safe_load(f)
            except yaml.YAMLError as e:
                print("Error when loading the server configuration:")
                print(e)

    @classmethod
    def get_server_root(cls) -> str:
        conf: dict = cls.get_server_conf()["app"]

        return f"http://{conf['host']}:{conf['port']}"
