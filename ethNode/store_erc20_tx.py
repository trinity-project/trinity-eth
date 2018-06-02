#!/usr/bin/env python
# coding=utf-8
import json
import os
import binascii
from decimal import Decimal
import time
import pymysql
import requests

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Numeric,Boolean,create_engine
from sqlalchemy.orm import sessionmaker
from config import setting


pymysql.install_as_MySQLdb()
engine = create_engine('mysql://%s:%s@%s/%s' %(setting.MYSQLDATABASE["user"],
                                               setting.MYSQLDATABASE["passwd"],
                                               setting.MYSQLDATABASE["host"],
                                               setting.MYSQLDATABASE["db"]),
                       pool_size=5)
Session = sessionmaker(bind=engine)
Base = declarative_base()
session=Session()

class Erc20Tx(Base):
    __tablename__ = 'erc20_tx'
    id = Column(Integer, primary_key=True)
    tx_id = Column(String(256))
    block_number = Column(Integer)
    contract = Column(String(64))
    address_from = Column(String(64))
    address_to = Column(String(64))
    value = Column(Numeric(16,8))
    block_timestamp=Column(Integer)
    hash_pushed=Column(Boolean,default=False)


    @staticmethod
    def save(tx_id,contract,address_from,address_to,value,block_number,block_timestamp):
        new_instance = Erc20Tx(tx_id=tx_id,
                                contract=contract,
                               address_from=address_from,
                                address_to=address_to,
                               value=value,
                               block_number=block_number,
                               block_timestamp=block_timestamp)
        session.add(new_instance)
        try:
            session.commit()
        except:
            session.rollback()

class LocalBlockCout(Base):
    __tablename__ = 'local_block_count'
    id = Column(Integer, primary_key=True)
    height = Column(Integer)


Base.metadata.create_all(engine)












def getblock(blockNumber):

    data = {
          "jsonrpc": "2.0",
          "method": "eth_getBlockByNumber",
          "params": [blockNumber,True],
          "id": 1
}
    res = requests.post(setting.ETH_URL,json=data).json()
    return res


def get_receipt_status(txId):

    data = {
          "jsonrpc": "2.0",
          "method": "eth_getTransactionReceipt",
          "params": [txId],
          "id": 1
}
    res = requests.post(setting.ETH_URL,json=data).json()
    return res["status"]


localBlockCount = session.query(LocalBlockCout).first()
if localBlockCount:

    local_block_count=localBlockCount.height
else:
    local_block_count=1
    localBlockCount=LocalBlockCout(height=local_block_count)
    session.add(localBlockCount)
    session.commit()

while True:
    # time.sleep(0.01)
    print (local_block_count)
    try:

        block_info=getblock(hex(local_block_count))
        if block_info["result"]["transactions"]:
            for tx in block_info["result"]["transactions"]:
                if tx["to"]==setting.CONTRACT_ADDRESS:
                    status=get_receipt_status(tx["hash"])
                    print(status)
                    if status:
                        address_to = "0x"+tx["input"][34:74]
                        value = int(tx["input"][74:], 16)/(10**8)
                        address_from=tx["from"]
                        block_number=int(tx["blockNumber"],16)
                        block_timestamp=int(block_info["result"]["timestamp"],16)
                        tx_id=tx["hash"]
                        try:
                            Erc20Tx.save(tx_id,setting.CONTRACT_ADDRESS,address_from,
                                     address_to,value,block_number,block_timestamp)
                        except Exception as e:
                            pass

                    else:
                        pass
        local_block_count+=1
        localBlockCount.height=local_block_count
        session.add(localBlockCount)
        session.commit()

    except Exception as e:
        print(e)
        time.sleep(15)





