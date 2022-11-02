#!/bin/sh
SCRIPTPATH=$(dirname $0)

. ${SCRIPTPATH}/env.sh
python3 ${SCRIPTPATH}/../app.py --debug --logger
