FROM ubuntu:22.10

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev libgeos-dev gdal-bin libgdal-dev

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

ENTRYPOINT [ "python3" ]

EXPOSE 5000
CMD [ "app.py" ]
