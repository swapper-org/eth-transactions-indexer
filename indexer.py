#!/usr/bin/python3
from os import environ
from web3 import Web3
from web3.middleware import geth_poa_middleware
import psycopg2
import logging
import time
import signal


# Logging configuration

logger = logging.getLogger("eth-indexer.log")
logger.setLevel(logging.INFO)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Safe close


def signalHandler(signum, frame):
    logger.info("Shutting down indexing process")


signal.signal(signal.SIGINT, signalHandler)


def main():

    dbName = environ.get("DB_NAME")
    startBlock = environ.get("START_BLOCK", "1")
    confirmations = environ.get("CONFIRMATIONS", "0")
    nodeUrl = environ.get("NODE_URL")
    period = environ.get("PERIOD", "20")

    logger.info("Running indexer with following configuration")
    logger.info(f"DB_NAME: {dbName}")
    logger.info(f"NODE_URL: {nodeUrl}")
    logger.info(f"START_BLOCK: {startBlock}")
    logger.info(f"CONFIRMATIONS: {confirmations}")
    logger.info(f"PERIOD: {period}")

    if dbName is None:
        logger.error('Postgres database url not defined. Please, define DB_NAME environment variable.')
        exit(2)

    if nodeUrl is None:
        logger.error('Node url not defined. Please, define NODE_URL environment variable.')
        exit(2)

    # Node connection

    logger.info(f"Connecting to {nodeUrl}")

    if nodeUrl.startswith("http"):
        web3 = Web3(Web3.HTTPProvider(nodeUrl))
    elif nodeUrl.startswith("ws"):
        web3 = Web3(Web3.WebsocketProvider(nodeUrl))
    else:
        web3 = Web3(Web3.IPCProvider(nodeUrl))

    web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if not web3.isConnected():
        logger.info(f"Can not connect to node url {nodeUrl}")
        exit(2)

    logger.info(f"Connected to {nodeUrl}")

    # Database connection

    logger.info(f"Connecting to {dbName}")

    try:
        conn = psycopg2.connect(dbName)
        conn.autocommit = True
        logger.info(f"Connected to {dbName}")
    except Exception as e:
        logger.info(f"Can not connect to database {dbName}")
        logger.info(e)
        exit(2)

    # Delete last block, it may be not fully indexed

    cur = conn.cursor()
    cur.execute("DELETE FROM public.ethtxs WHERE block = (SELECT Max(block) from public.ethtxs)")
    cur.close()
    conn.close()

    # Wait until node is synchronized

    while web3.eth.syncing:
        time.sleep(300)

    logger.info("Node is synchronised. ")

    while True:

        try:
            conn = psycopg2.connect(dbName)
            conn.autocommit = True
            logger.info(f"Connected to {dbName}")
        except Exception as e:
            logger.info(f"Can not connect to database {dbName}")
            logger.info(e)
            exit(2)

        cur = conn.cursor()
        cur.execute("SELECT Max(block) FROM public.ethtxs")
        currentBlock = cur.fetchone()[0]

        if currentBlock is None:
            currentBlock = int(startBlock)

        endBlock = int(web3.eth.block_number) - int(confirmations)

        logger.info(f"Current block in index {currentBlock}. Current block in ETH chain: {endBlock}")

        for blockNumber in range(currentBlock, endBlock):

            numTxs = web3.eth.getBlockTransactionCount(blockNumber)

            if numTxs > 0:
                insertBlockTransactions(web3=web3, blockNumber=blockNumber, numTxs=numTxs, cur=cur)
            else:
                logger.debug(f"Block {blockNumber} with no transactions")

        cur.close()
        conn.close()
        time.sleep(int(period))

def insertBlockTransactions(web3, cur, blockNumber, numTxs):

    blockTime = web3.eth.getBlock(blockNumber)["timestamp"]

    for txIndex in range(0, numTxs):

        tx = web3.eth.getTransactionByBlock(blockNumber, txIndex)

        # Check if transaction is a contract transfer
        if tx["value"] == 0 and not tx["input"].startswith("0xa9059cbb"):
            continue

        txReceipt = web3.eth.get_transaction_receipt(tx["hash"])

        # Pre-byzantium transactions do not have status field
        status = None
        if "status" in txReceipt:
            status = bool(txReceipt.status)

        # Contract transaction
        contractTo = ""
        contractValue = ""

        if tx["input"].startswith("0xa9059cbb"):
            contractTo = tx["input"][10:-64]
            contractValue = tx["input"][74:]

        if len(contractTo) > 128:
            logger.info(f"Skipping {tx['hash'].hex()} tx. Incorrect contract_to length: {len(contractTo)}")
            contractTo = ""
            contractValue = ""

        cur.execute(
           'INSERT INTO public.ethtxs(time, txfrom, txto, value, gas, gasprice, block, txhash, contract_to, contract_value, status, data) '
           'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) '
           'ON CONFLICT (txhash) '
           'DO UPDATE SET '
           'time = EXCLUDED.time, '
           'txfrom = EXCLUDED.txfrom, '
           'txto = EXCLUDED.txto, '
           'gas = EXCLUDED.gas, '
           'gasprice = EXCLUDED.gasprice, '
           'block = EXCLUDED.block, '
           'value = EXCLUDED.value, '
           'contract_to = EXCLUDED.contract_to, '
           'contract_value = EXCLUDED.contract_value, '
           'status = EXCLUDED.status, '
           'data = EXCLUDED.data',
           (blockTime, tx["from"], tx["to"], tx["value"], txReceipt["gasUsed"], tx["gasPrice"], blockNumber, tx["hash"].hex(), contractTo, contractValue, status, tx["input"]))


if __name__ == "__main__":
    main()
