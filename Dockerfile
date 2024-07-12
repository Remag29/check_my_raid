FROM python:3.13.0b2-slim

WORKDIR /app

COPY main.py .
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

CMD ["python", "-u", "./main.py"]