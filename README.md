# ETH-Transactions-Indexer

**ETH-Transactions-Indexer** is a service that allows you to store ETH and ERC20 transactions in a Postgres database to get insights of them.

This repository only contains the python code that indexs the transactions into the Postgres database. ETH node and Postgres database management is out of this repository, althought [database schema]([db-schema.sql](https://github.com/swapper-org/eth-transactions-indexer/blob/main/db-schema.sql)) is provided.


# Workflow

Application workflow

1. Node connection using [Web.py](https://web3py.readthedocs.io/en/stable/)
2. Postgres database connection using [psycopg2](https://www.psycopg.org)
3. Wait until node is fully synchronised
4. Indexing proccess from the selected block or if it had been started previously and some transactions were already indexed into the database, from the previous last indexed block


# Stored information

Indexed transactions included the following information:

- `time` is transaction timestamp.
- `txfrom` sender's Ethereum address.
- `txto` recipient's Ethereim address.
- `value` is the amount of Ethreum transferred.
- `gas` is the gas used.
- `gasPrice` is the gas price.
- `block` is the block number.
- `txhash` is the transaction hash.
- `contract_to` recipient's Ethereum address in case of conotract.
- `contract_value` is the amount transfered of ERC20 tranction in its token.
- `status` is the transaction status introduce in the Byzantium fork of Ethereum, it indicates if the top-level call succeded or failed. For Pre-bizantium transactions value is null


# Setup

**ETH-Transactions-Indexer** can be configured with the following environment varibles:

- `DB_NAME`: Postgres url of the database with the neccesary [schema](db-schema.sql). It's mandatory.
- `NODE_URL`: Ethereum node url. It's mandatory. The following providers are suppoorted:
  - IPC: Uses local file system, it is the fastest and the most secure.
  - WS: Works remotely, it faster than the HTTP
  - HTTP: More nodes supoport it
- `START_BLOCK`: First block to index. It's optional annd default value is 1.
- `CONFIRMATIONS`: Number of blocks to leave out of the indexing process from the last block. It's optional and default value is 0.
- `PERIOD`: Number of seconds between requesting the node which is the last block. It's optional and default value is 20 seconds.

## Running locally

To run **ETH-Transactions-Indexer** locally install the requirements using the following command.

```
pip3 install -r requirements.txt
```

To avoid python module conflicts, it is highly recommend to create a python virtual environment


# Docker

**ETH-Transactions-Indexer** has a public image in [Docker Hub](https://hub.docker.com/r/nodechain/eth-transactions-indexer).

# Dependencies

- Python 3.6
- Web3.py
- Psycopg2

# Reference


## Contributing

Please read [Contribution Guidelines](https://github.com/swapper-org/eth-transactions-indexer/blob/main/CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

# License

