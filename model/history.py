# --*-- coding : utf-8 --*--
"""Author: Trinity Core Team

MIT License

Copyright (c) 2018 Trinity

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""
from .manager import DBManager, rpc_response, connection_singleton


class TBLHistory(DBManager):
    """
        Descriptions    :
        Created         : 2018-02-13
        Modified        : 2018-03-21
    """
    def add_one(self, **kwargs):
        # to check whether the state is correct:
        return super(TBLHistory, self).add(*kwargs)

    @property
    @connection_singleton
    def client(self):
        return super(TBLHistory, self).client

    @property
    def db_table(self):
        return self.client.trans_db.get_collection(self.collection)

    def set_collection(self, collection):
        self.collection = collection

    @property
    def primary_key(self):
        return 'transaction'



class APITransaction(object):
    table = TBLHistory()

    @classmethod
    def get_transation(cls, history_index):
        cls.table = TBLHistory().set_collection(history_index)

    @classmethod
    @rpc_response('AddTransaction')
    def add_transaction(cls, *args):
        return cls.table.add_one(*args)

    @classmethod
    @rpc_response('DeleteTransaction')
    def delete_transaction(cls, transaction):
        return cls.table.delete_one(transaction)

    @classmethod
    @rpc_response('BatchDeleteTransaction')
    def batch_delete_transaction(cls, filters):
        return cls.table.delete_many(filters)

    @classmethod
    @rpc_response('QueryTransaction')
    def query_transaction(cls, transaction, *args, **kwargs):
        return cls.table.query_one(transaction, *args, **kwargs)

    @classmethod
    @rpc_response('BatchQueryTransaction')
    def batch_query_transaction(cls, filters, *args, **kwargs):
        return cls.table.query_many(filters, *args, **kwargs)

    @classmethod
    @rpc_response('UpdateTransaction')
    def update_transaction(cls, transaction, **kwargs):
        return cls.table.update_one(transaction, **kwargs)

    @classmethod
    @rpc_response('BatchUpdateTransaction')
    def batch_update_transaction(cls, filters, **kwargs):
        return cls.table.update_many(filters, **kwargs)
