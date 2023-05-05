#!/usr/bin/python3

import json

import uvicorn
from fastapi import FastAPI

from datacube.core.cache.cache_manager import CacheManager
from datacube.core.logging.logger import CustomLogger as Logger
from datacube.rest import ROUTERS
from datacube.rest.server.server_configuration import ServerConfiguration

LOGGER_CONFIG_FILE = "configs/logging.json"


if __name__ == "__main__":
    with open(LOGGER_CONFIG_FILE, "r") as f:
        Logger.register_logger(json.load(f))

    conf = ServerConfiguration.get_server_conf()

    # Create app and add routes
    app = FastAPI(debug=conf.dc3_builder.debug)

    for router in ROUTERS:
        app.include_router(router)

    # Set up logger
    if not conf.dc3_builder.debug:
        Logger.get_logger().setLevel("WARN")

    # Change hazelcast host if specified
    if conf.hazelcast:
        CacheManager.set_host(conf.hazelcast.host)

    # Check if app is connected to Hazelcast
    CacheManager()
    Logger.get_logger().info("Connected to Hazelcast cache manager")

    uvicorn.run(app, host=conf.dc3_builder.host,
                port=conf.dc3_builder.port)
