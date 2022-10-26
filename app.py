#!/usr/bin/python3

import argparse

from flask import Flask

from rest_api import api


class App:
    def __init__(self):
        self.app = Flask(__name__)
        api.init_app(self.app)

    def run(self, debug: bool = False):
        self.app.run(debug=debug)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Flask app for DataCube Builder")
    parser.add_argument("--debug", dest="debug", nargs="?",
                        const=True, default=False,
                        help="Enable debug mode")
    args = parser.parse_args()

    app = App()
    app.run(debug=args.debug)
