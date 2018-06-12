import pymysql

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String,create_engine, Text
from sqlalchemy.orm import sessionmaker
from config import setting
from project_log import setup_mylogger

logger=setup_mylogger(logfile="../log/store_account_info.log")

pymysql.install_as_MySQLdb()
engine = create_engine('mysql://%s:%s@%s/%s' %(setting.MYSQLDATABASE["user"],
                                               setting.MYSQLDATABASE["passwd"],
                                               setting.MYSQLDATABASE["host"],
                                               setting.MYSQLDATABASE["db_block_info"]),
                       )

Session = sessionmaker(bind=engine)
Base = declarative_base()


class Tx(Base):
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
    block_number = Column(String(16))
    block_timestamp=Column(String(16))


    @staticmethod
    def save(tx_id,address_from,address_to,value,gas,gas_price,nonce,data,block_number,block_timestamp):
        new_instance = Tx(tx_id=tx_id,
                               address_from=address_from,
                                address_to=address_to,
                               value=value,
                               gas=gas,
                               gas_price=gas_price,
                               nonce=nonce,
                               data=data,
                               block_number=block_number,
                               block_timestamp=block_timestamp)
        session=Session()
        session.add(new_instance)
        try:
            session.commit()
        except Exception as e:
            logger.error(e)
            session.rollback()
        finally:
            session.close()

class LocalBlockCout(Base):
    __tablename__ = 'local_block_count'
    id = Column(Integer, primary_key=True)
    height = Column(Integer)

    @staticmethod
    def query():
        session=Session()
        exist_instance=session.query(LocalBlockCout).first()
        session.close()
        return exist_instance
    @staticmethod
    def save(height):
        session=Session()
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
        session=Session()
        session.add(exist_instance)
        try:
            session.commit()
        except:
            session.rollback()
        finally:
            session.close()


Base.metadata.create_all(engine)