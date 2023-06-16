#!/bin/sh
SCRIPTPATH=$(dirname $0)

echo "Starting the datacube builder..."
. ${SCRIPTPATH}/env.sh
python3 ${SCRIPTPATH}/../app.py --debug
