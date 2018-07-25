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


class TBLTransaction(DBManager):
    """
        Descriptions    :
        Created         : 2018-02-13
        Modified        : 2018-03-21
    """
    def add_one(self, **kwargs):
        # to check whether the state is correct:
        return super(TBLTransaction, self).add(**kwargs)

    @property
    @connection_singleton
    def client(self):
        return super(TBLTransaction, self).client

    @property
    def db_table(self):
        return self.client.trans_db.get_collection(self.collection)

    def set_collection(self, collection):
        self.collection = collection

    @property
    def primary_key(self):
        return 'nonce'

    def list_collections(self):
        return self.client.trans_db.list_collection_names()

    def delete_collection(self, collection_index):
        return self.client.trans_db.drop_collection(collection_index)



class APITransaction(object):
    table = TBLTransaction()

    def __init__(self, transaction_index):
        TBLTransaction().set_collection(transaction_index)

    def add_transaction(self, **kwargs):
        return self.table.add_one(**kwargs)

    def delete_transaction(self, transaction):
        return self.table.delete_one(transaction)

    def batch_delete_transaction(self, filters):
        return self.table.delete_many(filters)

    def query_transaction(self, transaction, *args, **kwargs):
        return self.table.query_one(transaction, *args, **kwargs)

    def batch_query_transaction(self, filters, *args, **kwargs):
        return self.table.query_many(filters, *args, **kwargs)

    def update_transaction(self, transaction, **kwargs):
        return self.table.update_one(transaction, **kwargs)

    def batch_update_transaction(self, filters, **kwargs):
        return self.table.update_many(filters, **kwargs)
