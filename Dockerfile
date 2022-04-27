FROM python:3.6-slim

RUN apt update -y
RUN apt install -y build-essential
RUN apt install -y git
RUN pip3 install web3
RUN pip3 install psycopg2

RUN mkdir /eth-indexer
COPY ./indexer.py /eth-indexer

WORKDIR /eth-indexer
ENTRYPOINT ["python3.6", "./indexer.py"]
