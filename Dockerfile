FROM ubuntu:22.10

RUN apt-get update -y && \
    apt-get install -y curl python3-pip python3-dev libgeos-dev gdal-bin libgdal-dev imagemagick

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY ./app.py /app/app.py
COPY ./datacube /app/datacube
COPY ./assets /app/assets

ENTRYPOINT [ "python3" ]

EXPOSE 5000
CMD [ "app.py"]
