FROM ubuntu:22.10

RUN apt-get update -y && \
    apt-get install -y curl python3-pip python3-dev libgeos-dev gdal-bin libgdal-dev

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY ./app.py /app/app.py
COPY ./configs /app/configs
COPY ./datacube /app/datacube

ENTRYPOINT [ "python3" ]

EXPOSE 5000
CMD [ "app.py" , "--host", "0.0.0.0"]
