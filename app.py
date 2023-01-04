#!/usr/bin/python3

import argparse
import logging
from flask import Flask
from rest_api import api


class App:
    def __init__(self, loggerLevel):
        self.app = Flask(__name__)
        self.app.logger.setLevel(loggerLevel)
        api.init_app(self.app)

    def run(self, debug: bool = False, host="127.0.0.1"):
        self.app.run(debug=debug, host=host)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Flask app for DataCube Builder")
    parser.add_argument("--debug", dest="debug", nargs="?",
                        const=True, default=False,
                        help="Enable debug mode")
    parser.add_argument("--logger", dest="isLogger", nargs="?",
                        const=True, default=False,
                        help="Enable INFO level logging")
    parser.add_argument("--host", dest="host",
                        default="127.0.0.1",
                        help="Set the host of the app. By default localhost.")
    
    args = parser.parse_args()
    loggerLevel = logging.INFO if args.isLogger else logging.ERROR
    
    app = App(loggerLevel)
    app.run(debug=args.debug, host=args.host)
