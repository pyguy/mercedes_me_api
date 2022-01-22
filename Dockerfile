FROM python:3.9-alpine3.15

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./prometheus_exporter.py" ]
