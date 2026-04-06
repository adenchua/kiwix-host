FROM python:3.14

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY download.py .
COPY sotoki_wrapper.py .

ENTRYPOINT ["python", "download.py"]
