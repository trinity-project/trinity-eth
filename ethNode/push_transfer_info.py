#!/usr/bin/env python
# coding=utf-8

import time
import pymysql
import requests

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Numeric, Boolean, create_engine, or_
from sqlalchemy.orm import sessionmaker
from config import setting

from logzero import logger,logfile

logfile("push_transfer.log", maxBytes=1e6, backupCount=3)

pymysql.install_as_MySQLdb()
engine = create_engine('mysql://%s:%s@%s/%s' %(setting.MYSQLDATABASE["user"],
                                               setting.MYSQLDATABASE["passwd"],
                                               setting.MYSQLDATABASE["host"],
                                               setting.MYSQLDATABASE["db"]),
                       pool_size=5)

Session = sessionmaker(bind=engine)
Base = declarative_base()


class Erc20Tx(Base):
    __tablename__ = 'erc20_tx'
    id = Column(Integer, primary_key=True)
    tx_id = Column(String(256),unique=True)
    block_number = Column(Integer)
    contract = Column(String(64))
    address_from = Column(String(64),index=True)
    address_to = Column(String(64),index=True)
    value = Column(Numeric(16,8))
    block_timestamp=Column(Integer)
    has_pushed=Column(Boolean,default=False)

    @staticmethod
    def save(self,session):
        try:
            session.add(self)
            session.commit()
        except:
            session.roolback()
        finally:
            session.close()

def push_transfer(txId,addressFrom,addressTo,value,blockTimestamp):
    headers={
        "Password":"!QWWpigxo1970q~"
    }
    data = {
        "txId":txId,
        "addressFrom": addressFrom,
        "addressTo": addressTo,
        "value": str(value),
        "blockTimestamp":blockTimestamp
    }
    try:
        res = requests.post(setting.WEBAPI, json=data,headers=headers).json()
        return res["Code"]
    except:
        return None

def TransferMonitor():


    while True:
        session = Session()
        exist_instance = session.query(Erc20Tx).filter(
            or_(Erc20Tx.address_from == setting.FUNDING_ADDRESS,
                Erc20Tx.address_to == setting.FUNDING_ADDRESS),
            Erc20Tx.has_pushed==0
        ).first()
        if exist_instance:
            res=push_transfer(exist_instance.tx_id,
                              exist_instance.address_from,
                              exist_instance.address_to,
                              exist_instance.value,
                              exist_instance.block_timestamp)

            if res==0:
                exist_instance.has_pushed=1
                Erc20Tx.save(exist_instance,session)
                logger.info("push tx:{} sucess".format(exist_instance.tx_id))
                # time.sleep(3)
            else:
                logger.info("push tx:{} fail".format(exist_instance.tx_id))
                time.sleep(3)
        else:
            session.close()
            time.sleep(30)

if __name__ == "__main__":
    TransferMonitor()