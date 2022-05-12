FROM python:3.9
WORKDIR /app

COPY . /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && apt-get install -y --no-install-recommends gcc \
    && apt-get install -y --no-install-recommends cmake \
    && apt-get purge -y --auto-remove


RUN pip3 install git+https://github.com/EnzymeML/PyEnzyme.git
RUN pip3 install fastapi uvicorn jinja2

COPY pyenzyme_server.py /app

CMD ["uvicorn", "pyenzyme_server:app", "--host", "0.0.0.0", "--port", "80"]