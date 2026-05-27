FROM python:3.11-slim

WORKDIR /app

COPY server/requirements-server.txt /app/requirements-server.txt
RUN pip install --no-cache-dir -r /app/requirements-server.txt

COPY shared /app/shared
COPY server /app/server

ENV PYTHONUNBUFFERED=1

EXPOSE 65432

CMD ["python", "server/server.py"]
