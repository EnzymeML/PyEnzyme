FROM python:3.7-slim
WORKDIR /app
COPY requirements.txt /app
RUN pip3 install -r requirements.txt --no-cache-dir
ADD pyenzyme /app/pyenzyme
COPY /pyenzyme/Examples/restful/run_server.py /app
ENTRYPOINT ["python3"]
CMD ["run_server.py"]