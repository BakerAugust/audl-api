FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim

COPY requirements.txt /code/requirements.txt

RUN pip install -r /code/requirements.txt

COPY ./app /app