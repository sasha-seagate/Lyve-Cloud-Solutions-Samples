FROM python:3.10-slim
LABEL version="1.0"
LABEL description="The Lyve Cloud Log Gateway"
LABEL authors="Seagate Technology Holdings plc"

WORKDIR /app

ADD requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

ADD . /app

CMD ["python", "main.py"]
