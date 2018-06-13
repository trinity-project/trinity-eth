#!/usr/bin/env python
# coding=utf-8

import time
import requests

from data_model.block_info_model import Tx,LocalBlockCout,logger

from config import setting


def getblock(blockNumber):

    data = {
          "jsonrpc": "2.0",
          "method": "eth_getBlockByNumber",
          "params": [blockNumber,True],
          "id": 1
}

    try:
        res = requests.post(setting.ETH_URL,json=data).json()
        return res["result"]
    except:
        return None



localBlockCount = LocalBlockCout.query()
if localBlockCount:
    local_block_count=localBlockCount.height
else:
    local_block_count=0

    localBlockCount=LocalBlockCout(height=local_block_count)


while True:
    logger.info(local_block_count)
    block_info=getblock(hex(local_block_count))
    if not block_info:
        time.sleep(15)
        continue
    if block_info["transactions"]:
        for tx in block_info["transactions"]:
            tx_id=tx.get("hash")
            address_from=tx.get("from")
            address_to=tx.get("to")
            value=tx.get("value")
            gas=tx.get("gas")
            gas_price=tx.get("gasPrice")
            nonce=tx.get("nonce")
            data=tx.get("input")
            block_number=tx.get("blockNumber")
            block_timestamp=block_info.get("timestamp")


            Tx.save(tx_id,address_from,address_to,value,gas,gas_price,nonce,data,block_number,block_timestamp)

    local_block_count+=1
    localBlockCount.height=local_block_count
    LocalBlockCout.update(localBlockCount)







