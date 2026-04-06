FROM python:3.14

WORKDIR /app

RUN apt-get update && apt-get install -y redis-server && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY download.py .
COPY sotoki_wrapper.py .
COPY entrypoint.sh .

ENTRYPOINT ["bash", "entrypoint.sh"]
