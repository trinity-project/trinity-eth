#!/usr/bin/env python
# coding=utf-8

import requests
import time

from config import setting
from data_model.account_info_model import LocalBlockCout,Tx,Erc20Tx,EthTx,BlockHeight,logger
from decimal import Decimal


def get_receipt_status(txId,retry_num=3):

    data = {
          "jsonrpc": "2.0",
          "method": "eth_getTransactionReceipt",
          "params": [txId],
          "id": 1
}
    try:
        res = requests.post(setting.ETH_URL,json=data).json()
        return res["result"]
    except Exception as e:
        retry_num-=1
        if retry_num==0:
            logger.error("txId:{} get transaction receipt fail \n {}".format(tx["hash"], e))
            return None
        return get_receipt_status(txId,retry_num)





localBlockCount = LocalBlockCout.query()
if localBlockCount:
    local_block_count=localBlockCount.height
else:
    local_block_count=0

    localBlockCount=LocalBlockCout(height=local_block_count)


while True:
    logger.info(local_block_count)
    block_h=BlockHeight.query()
    if not block_h:
        continue

    if local_block_count<=block_h.height:
        exist_instance=Tx.query(local_block_count)
        if exist_instance:
            for tx in exist_instance:
                tx_id = tx.tx_id
                address_from = tx.address_from
                address_to = tx.address_to
                value = int(tx.value,16)
                gas = int(tx.gas,16)
                gas_price = Decimal(str(int(tx.gas_price,16)/(10**18)))
                nonce = int(tx.nonce,16)
                data = tx.data
                block_number = tx.block_number
                block_timestamp = int(tx.block_timestamp,16)

                res = get_receipt_status(tx.tx_id)
                if res:
                    state=int(res.get("status"),16) if res.get("status") else None
                else:
                    logger.info("txId:{} get transction receipt  fail".format(tx_id))
                    state=None
                if data=="0x":
                    value=Decimal(str(value/(10**18)))
                    EthTx.save(tx_id,address_from,address_to,value,gas,gas_price,nonce,block_number,block_timestamp,state)

                else:
                    if address_to==setting.CONTRACT_ADDRESS and data[:10]=="0xa9059cbb":
                        address_to = "0x"+data[34:74]
                        value = Decimal(str(int(data[74:], 16)/(10**8)))
                        logger.info(tx_id,address_from,address_to,value,gas,gas_price,nonce,block_number,block_timestamp,state)
                        Erc20Tx.save(tx_id,address_from,address_to,value,gas,gas_price,nonce,block_number,block_timestamp,state)

        local_block_count+=1
        localBlockCount.height=local_block_count
        LocalBlockCout.update(localBlockCount)

    else:
        time.sleep(15)





