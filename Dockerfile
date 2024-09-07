FROM python:3.11.9-slim-bullseye

RUN apt-get update
RUN pip install poetry

WORKDIR /app
COPY . /app

RUN poetry install --with tests

ENTRYPOINT ["poetry", "run", "pytest", "-vv"]