FROM python:3.9-slim-buster

WORKDIR /usr/src/app

COPY . .

RUN python3 -m ensurepip
RUN pip install -r requirements.txt

# RUN ./script.sh
