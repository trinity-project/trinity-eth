#!/usr/bin/env python
# encoding: utf-8
"""
@author: Maiganne

"""


from . import db


class Erc20Tx(db.Model):
    __tablename__ = 'erc20_tx'
    id = db.Column(db.Integer, primary_key=True)
    tx_id = db.Column(db.String(256))
    block_number = db.Column(db.Integer)
    contract = db.Column(db.String(64))
    address_from = db.Column(db.String(64))
    address_to = db.Column(db.String(64))
    value = db.Column(db.Numeric(16,8))
    block_timestamp=db.Column(db.Integer)



    @staticmethod
    def save(tx_id,contract,address_from,address_to,value,block_number,block_timestamp):
        new_instance = Erc20Tx(tx_id=tx_id,
                                contract=contract,address_from=address_from,
                                address_to=address_to,value=value,block_number=block_number,
                               block_timestamp=block_timestamp)
        db.session.add(new_instance)
        db.session.commit()