FROM python:3.7-slim

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY setup setup
COPY helpers.py helpers.py
COPY afisha_dev_bot.py afisha_dev_bot.py

CMD ["python", "./afisha_dev_bot.py"]
