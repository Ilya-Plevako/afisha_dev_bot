FROM python:3.7-slim

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY setup setup
COPY helpers.py helpers.py
COPY devbot.py devbot.py

CMD ["python", "./devbot.py"]
