FROM python:3.10

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY main.py .
COPY constants.py .
COPY rom/ rom/.
COPY cogs/ cogs/.
COPY util/ util/.

ENTRYPOINT ["python3", "main.py"]
