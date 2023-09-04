#!/bin/bash

IMAGE=arlas-datacube-builder
[ -z "$1" ] && echo "Please provide the version" && exit 1;
VERSION=$1
echo "Build and releas the image with version ${VERSION}"

echo "Building the image ..."
docker build -t gisaia/${IMAGE}:${VERSION} -t gisaia/${IMAGE}:latest .

echo "Publishing the image ..."
docker login
docker push gisaia/${IMAGE}:latest
docker push gisaia/${IMAGE}:${VERSION}

git tag -a ${VERSION} -m "ARLAS Earth Analytics Datacube Builder ${VERSION}"
git push origin ${VERSION}
