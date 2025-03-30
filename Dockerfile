FROM python:3.14-rc-alpine3.21

WORKDIR /app

COPY main.py .
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

CMD ["python", "-u", "./main.py"]