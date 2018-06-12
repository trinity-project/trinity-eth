import json
import os
import binascii
from decimal import Decimal
import time
import pymysql
import requests

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Numeric, Boolean, create_engine, DECIMAL, Text
from sqlalchemy.orm import sessionmaker
from config import setting


from project_log import setup_mylogger

logger=setup_mylogger(logfile="../log/store_account_info.log")

pymysql.install_as_MySQLdb()

block_info_engine = create_engine('mysql://%s:%s@%s/%s' %(setting.MYSQLDATABASE["user"],
                                               setting.MYSQLDATABASE["passwd"],
                                               setting.MYSQLDATABASE["host"],
                                               setting.MYSQLDATABASE["db_block_info"]),
                                  pool_recycle=3600,pool_size=100
                                  )

account_info_engine = create_engine('mysql://%s:%s@%s/%s' %(setting.MYSQLDATABASE["user"],
                                               setting.MYSQLDATABASE["passwd"],
                                               setting.MYSQLDATABASE["host"],
                                               setting.MYSQLDATABASE["db_account_info"]),
                                    pool_recycle=3600,pool_size=100
                                    )

BlockInfoSession = sessionmaker(bind=block_info_engine)
AccountInfoSession = sessionmaker(bind=account_info_engine)

BlockInfoBase = declarative_base()
AccountInfoBase = declarative_base()

class Erc20Tx(AccountInfoBase):
    __tablename__ = 'erc20_tx'
    id = Column(Integer, primary_key=True)
    tx_id = Column(String(66),unique=True)
    contract = Column(String(64))
    address_from = Column(String(64),index=True)
    address_to = Column(String(64),index=True)
    value = Column(DECIMAL(17,8))
    gas = Column(Integer)
    gas_price = Column(Integer)
    nonce = Column(Integer)
    block_number = Column(Integer)
    block_timestamp=Column(Integer)
    state = Column(Boolean)
    has_pushed=Column(Boolean,default=False)


    @staticmethod
    def save(tx_id,contract,address_from,address_to,value,gas,gas_price,nonce,block_number,block_timestamp,state):
        new_instance = Erc20Tx(tx_id=tx_id,
                                contract=contract,
                               address_from=address_from,
                                address_to=address_to,
                               value=value,
                               state=state,
                               gas=gas,
                               gas_price=gas_price,
                               nonce=nonce,
                               block_number=block_number,
                               block_timestamp=block_timestamp)
        session=AccountInfoSession()
        session.add(new_instance)
        try:
            session.commit()
        except:
            logger.error("store error txid:{},addressFrom:{},addressTo:{},value:{}".format(tx_id, address_from, address_to, value))
            session.rollback()
        finally:
            session.close()


class EthTx(AccountInfoBase):
    __tablename__ = 'eth_tx'
    id = Column(Integer, primary_key=True)
    tx_id = Column(String(66),unique=True)
    address_from = Column(String(64),index=True)
    address_to = Column(String(64),index=True)
    value = Column(DECIMAL(30,18))
    gas = Column(Integer)
    gas_price = Column(Integer)
    nonce = Column(Integer)
    block_number = Column(Integer)
    block_timestamp=Column(Integer)
    state = Column(Boolean)


    @staticmethod
    def save(tx_id,address_from,address_to,value,gas,gas_price,nonce,block_number,block_timestamp,state):
        new_instance = Erc20Tx(tx_id=tx_id,
                               address_from=address_from,
                                address_to=address_to,
                               value=value,
                               gas=gas,
                               gas_price=gas_price,
                               nonce=nonce,
                               block_number=block_number,
                               block_timestamp=block_timestamp,
                               state=state
                               )
        session=AccountInfoSession()
        session.add(new_instance)
        try:
            session.commit()
        except:
            logger.error("store error txid:{},addressFrom:{},addressTo:{},value:{}"
                         .format(tx_id, address_from, address_to, value))
            session.rollback()
        finally:
            session.close()

class LocalBlockCout(AccountInfoBase):
    __tablename__ = 'local_block_count'
    id = Column(Integer, primary_key=True)
    height = Column(Integer)

    @staticmethod
    def query():
        session=AccountInfoSession()
        exist_instance=session.query(LocalBlockCout).first()
        session.close()
        return exist_instance
    @staticmethod
    def save(height):
        session=AccountInfoSession()
        new_instance = LocalBlockCout(height=height)
        session.add(new_instance)
        try:
            session.commit()
        except:
            session.rollback()
        finally:
            session.close()
    @staticmethod
    def update(exist_instance):
        session=AccountInfoSession()
        session.add(exist_instance)
        try:
            session.commit()
        except:
            session.rollback()
        finally:
            session.close()



class Tx(BlockInfoBase):
    __tablename__ = 'tx'
    id = Column(Integer, primary_key=True)
    tx_id = Column(String(66),unique=True)
    address_from = Column(String(64),index=True)
    address_to = Column(String(64),index=True)
    value = Column(String(32))
    gas = Column(String(16))
    gas_price = Column(String(16))
    nonce = Column(String(16))
    data = Column(Text)
    block_number = Column(Integer)
    block_timestamp=Column(String(16))


    @staticmethod
    def query(block_height):
        session=BlockInfoSession()
        exist_instance=session.query(Tx).filter(Tx.block_number==block_height).all()
        session.close()
        return exist_instance

class BlockHeight(BlockInfoBase):
    __tablename__ = 'local_block_count'
    id = Column(Integer, primary_key=True)
    height = Column(Integer)

    @staticmethod
    def query():
        session=BlockInfoSession()
        exist_instance=session.query(LocalBlockCout).first()
        session.close()
        return exist_instance




AccountInfoBase.metadata.create_all(account_info_engine)
