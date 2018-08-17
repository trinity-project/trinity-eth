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
        return super(TBLHistory, self).add(**kwargs)

    @property
    @connection_singleton
    def client(self):
        return super(TBLHistory, self).client

    @property
    def db_table(self):
        return self.client.trans_db.get_collection(self.collection)

    def set_collection(self, collection):
        """

        :param collection:
        :return:
        """
        self.collection = collection

    @property
    def primary_key(self):
        return "tx_id"




class APIHistory(object):
    """

    """
    def __init__(self):
        self.table = TBLHistory()

    def set_history_collection(self, collection_index):
        """

        :param collection_index:
        :return:
        """
        self.table.set_collection(collection_index)


    def add_history(self, **args):
        """

        :param args:
        :return:
        """
        return self.table.add_one(**args)


    def query_history(self, transaction, *args, **kwargs):
        """

        :param transaction:
        :param args:
        :param kwargs:
        :return:
        """
        return self.table.query_one(transaction, *args, **kwargs)


    def batch_query_history(self, filters, *args, **kwargs):
        """

        :param filters:
        :param args:
        :param kwargs:
        :return:
        """
        return self.table.query_many(filters, *args, **kwargs)


    def update_history(self, tx_id, **kwargs):
        """

        :param tx_id:
        :param kwargs:
        :return:
        """
        return self.table.update_one(tx_id, **kwargs)

    def batch_update_history(self, filters, **kwargs):
        """

        :param filters:
        :param kwargs:
        :return:
        """
        return self.table.update_many(filters, **kwargs)
