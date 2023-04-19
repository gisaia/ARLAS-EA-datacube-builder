#!/usr/bin/python3

import json

import uvicorn
from fastapi import FastAPI

from datacube.core.logging.logger import CustomLogger as Logger
from datacube.rest import ROUTERS
from datacube.rest.serverConfiguration import ServerConfiguration

LOGGER_CONFIG_FILE = "configs/logging.json"


if __name__ == "__main__":
    with open(LOGGER_CONFIG_FILE, "r") as f:
        Logger.register_logger(json.load(f))

    conf = ServerConfiguration.get_server_conf()

    # Create app and define functions
    app = FastAPI(debug=conf["app"]["debug"])

    for router in ROUTERS:
        app.include_router(router)

    if not conf["app"]["debug"]:
        Logger.get_logger().setLevel("INFO")

    uvicorn.run(app, host=conf["app"]["host"],
                port=conf["app"]["port"])
