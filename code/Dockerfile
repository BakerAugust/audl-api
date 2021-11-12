FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim

ARG PY_VERSION=3.8

COPY requirements.txt /code/requirements.txt

RUN pip install -r /code/requirements.txt

WORKDIR /code
COPY ./app/ /app/