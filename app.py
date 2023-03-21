#!/usr/bin/python3

import argparse
import logging
from logging.config import dictConfig
import uvicorn
from fastapi import FastAPI
import json

from api_methods.build_cube import build_datacube

from models.request.cubeBuild import CubeBuildRequest, \
                                     TransformedCubeBuildRequest

LOGGER_CONFIG_FILE = "configs/logging.json"
LOGGER_NAME = "dc3-logger"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="FastAPI app for DataCube Builder")
    parser.add_argument("--debug", dest="debug", nargs="?",
                        const=True, default=False,
                        help="Enable debug mode")
    parser.add_argument("--host", dest="host",
                        default="127.0.0.1",
                        help="Set the host of the app. By default localhost.")
    parser.add_argument("--port", dest="port",
                        default=5000,
                        help="Set the port of the app. By default 5000.")
    args = parser.parse_args()

    with open(LOGGER_CONFIG_FILE, "r") as f:
        dictConfig(json.load(f))
    logger = logging.getLogger(LOGGER_NAME)

    # Create app and define functions
    app = FastAPI(debug=args.debug)

    @app.post("/cube/build")
    async def cube_build(request: CubeBuildRequest):
        build_datacube(TransformedCubeBuildRequest(request), logger)

    if not args.debug:
        logger.setLevel("INFO")

    uvicorn.run(app, host=args.host, port=args.port)
