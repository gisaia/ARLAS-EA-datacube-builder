#!/bin/sh
SCRIPTPATH=$(dirname $0)
HAZELCAST_CACHE=hazelcast/hazelcast:5.2

echo "Setting up the cache"
if docker ps | grep -q ${HAZELCAST_CACHE}; then
    echo "Hazelcast is already up"
else
    echo "Starting Hazelcast..."
    docker run -d -p 5701:5701 ${HAZELCAST_CACHE} > /dev/null
fi

echo "Starting the datacube builder..."
. ${SCRIPTPATH}/env.sh
python3 ${SCRIPTPATH}/../app.py --debug
