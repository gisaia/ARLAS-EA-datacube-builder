#!/usr/bin/python3

from flask import Flask
from flask_restx import Api

from rest_api import api

import argparse

class App:
    def __init__(self, api:Api):
        self.app = Flask(__name__)
        api.init_app(self.app)

    def run(self, debug:bool = False):
        self.app.run(debug=debug)

if __name__ =="__main__":
    parser = argparse.ArgumentParser(description="Flask app for DataCube Builder")
    parser.add_argument("--debug", dest="debug", nargs="?",
                        const=True, default=False,
                        help="Enable debug mode")
    args = parser.parse_args()

    app = App(api)
    app.run(debug=args.debug)
