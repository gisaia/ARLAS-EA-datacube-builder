#!/usr/bin/python3

import json
import os

import uvicorn
from fastapi import FastAPI

from datacube.core.cache.cache_manager import CACHE_DIR
from datacube.core.logging.logger import CustomLogger as Logger
from datacube.rest import ROUTERS
from datacube.rest.exception_handler import EXCEPTION_HANDLERS
from datacube.rest.server.server_configuration import ServerConfiguration

LOGGER_CONFIG_FILE = "configs/logging.json"


# Get server configuration
conf = ServerConfiguration.get_server_conf()


# Set up logger
with open(LOGGER_CONFIG_FILE, "r") as f:
    Logger.register_logger(json.load(f))
if not conf.dc3_builder.debug:
    Logger.get_logger().setLevel("WARN")


# Set up cache
if not os.path.exists(CACHE_DIR):
    os.mkdir(CACHE_DIR)
else:
    for f in os.listdir(CACHE_DIR):
        os.remove(os.path.join(CACHE_DIR, f))


# Create app and add routes
app = FastAPI(debug=conf.dc3_builder.debug)

for router in ROUTERS:
    app.include_router(router)

for eh in EXCEPTION_HANDLERS:
    app.add_exception_handler(eh.exception, eh.handler)

# Start app
uvicorn.run(app, host=conf.dc3_builder.host,
            port=conf.dc3_builder.port)
