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
from unittest import mock, TestCase
import mongomock

from model import manager
from model import address_model
from model import channel_model
from model import node_model
from model import transaction_model


def ut_db_congif(db_name: str):
    db_cfg = {
        'host': 'localhost',
        'channel': db_name,
        'port': 27017,
        'type': 'mongodb',
        'authentication': {
            'user': None,
            'password': None
        }
    }
    return mock.patch('model.manager.cfg', db_cfg)


class LOG(object):
    @staticmethod
    def critical(msg, *args, **kwargs):
        pass

    fatal = critical

    @staticmethod
    def error(msg, *args, **kwargs):
        pass

    @staticmethod
    def exception(msg, *args, exc_info=True, **kwargs):
        pass

    @staticmethod
    def warning(msg, *args, **kwargs):
        """

        :rtype: 
        """
        pass

    @staticmethod
    def warn(msg, *args, **kwargs):
        pass

    @staticmethod
    def info(msg, *args, **kwargs):
        pass

    @staticmethod
    def debug(msg, *args, **kwargs):
        pass


class MockDBClient(object):
    @property
    @mock.patch('pymongo.MongoClient', mongomock.MongoClient)
    def client(self):
        attr = "_{}__client".format(self.__class__.__name__)
        if not hasattr(self, attr):
            self.__setattr__(attr, manager.DBClient())

        return self.__getattribute__(attr)

    @property
    def database_name(self):
        return None


class DBTestBase(TestCase, MockDBClient):
    """"""
    def tearDown(self):
        super(DBTestBase, self).tearDown()

        # clear the database resources
        self.clear_resources()

    def clear_resources(self):
        if self.client.db_client:
            self.client.db_client.drop_database(self.database_name)
            self.client.close()


# *********************************************** Manager.py Unit Test *********************************************** #
manager_test_db = 'ManagerTestDatabase'


class DBClientTestBase(DBTestBase):
    """"""
    @property
    def database_name(self):
        return manager_test_db


@ut_db_congif(manager_test_db)
@mock.patch('manager.LOG', LOG)
class DBClientTest(DBClientTestBase):

    def test_DBClient_instance(self):
        self.assertIsNotNone(self.client.db_client)
        self.assertIsNotNone(self.client.db)

        self.assertEqual(self.client.db_name, self.database_name)
        self.assertEqual(self.client.uri, 'mongodb://localhost:27017/{}'.format(self.database_name))

    def test_close(self):
        self.client.db_client.drop_database(self.database_name)
        self.client.close()

        self.assertIsNone(self.client.db_client)
        self.assertIsNone(self.client.db)


# @ut_db_congif(manager_test_db)
# @mock.patch('manager.LOG', LOG)
# class DBManagerTest(DBClientTestBase):
#     pass


# @ut_db_congif(manager_test_db)
# @mock.patch('manager.LOG', LOG)
# class RPCResponseMethodTest(DBClientTestBase):
#     pass

# ******************************************** address_model.py Unit Test ******************************************** #
class MockTBLWalletAddress(MockDBClient, address_model.TBLWalletAddress):
    pass


class AddressModelTestBase(DBTestBase):
    def setUp(self):
        super(AddressModelTestBase, self).setUp()
        self.addr_inst = MockTBLWalletAddress()

        tests_addres_data = [['AFxEyaWvxYkehJqBjWVDPdZbCAZjJnznC3',
                              address_model.EnumChainType.NEO,
                              '6PYVUQaLs2vSK8qsUjCF41AzEr1shV7EcsTfiwuNYRDWafoNGpFyTyUzGn',
                              'node-1'],
                             ['AczJdApfD9sYK6DjB2qwUeWk4xy6HqgjnL',
                              address_model.EnumChainType.TNC,
                              '6PYXQrqcjbbLsmqR9a6U3oi82hKbotz4brKUiuREjcqQVevYWPmU1kdUpg',
                              'node-1'],
                             ['AMb9fDfRiQvSEbqC11Jq8kzaKVc4jRNgAY',
                              address_model.EnumChainType.NEO,
                              '6PYWr57eAf5xsU4A5e9pqZBCaJpdGXuS9QrxMdit1jZUg9TUiHLgmxJkwc',
                              'node-2'],
                             ['AQDpt385NDxLLSKsiyQmjmHPGQn1ZbvdNb',
                              address_model.EnumChainType.NEO,
                              '6PYVexaFJHFiSYyEYvaLaRxzmmNatZSayqs82cZ1fhTQwkDraURNAhKKXw',
                              'node-3']]


class TBLWalletAddressTest(AddressModelTestBase):
    def test__add_one(self):
        #address_model.TBLWalletAddress.add_one()
        pass

    def test__query_one(self):
        result = self.addr_inst.query_one({'node': 'node-1'})
        print (result)

        pass
    #
    # def test__(self):
    #     address_model.TBLWalletAddress


class APIWalletAddressTest(AddressModelTestBase):
    pass

# ******************************************** channel_model.py Unit Test ******************************************** #
channel_model_test_db = 'ChannelModelTestDatabase'


class ChannelModeTestBase(DBTestBase):
    @property
    def database_name(self):
        return channel_model_test_db


@ut_db_congif(channel_model_test_db)
class TBLChannelTest(ChannelModeTestBase):
    pass


@ut_db_congif(channel_model_test_db)
class APIChannelTest(ChannelModeTestBase):
    pass

# ******************************************** node_model.py Unit Test *********************************************** #
node_model_test_db = 'NodeModelTestDatabase'


class NodeModeTestBase(DBTestBase):
    @property
    def database_name(self):
        return node_model_test_db


@ut_db_congif(node_model_test_db)
class TBLNodeTest(DBTestBase):
    pass


@ut_db_congif(node_model_test_db)
class APINodeTest(DBTestBase):
    pass

# ******************************************** transaction_model.py Unit Test **************************************** #
transaction_model_test_db = 'TransactionModelTestDatabase'


class NodeModeTestBase(DBTestBase):
    @property
    def database_name(self):
        return transaction_model_test_db


@ut_db_congif(transaction_model_test_db)
class TBLTransactionTest(DBTestBase):
    pass


@ut_db_congif(transaction_model_test_db)
class APITransactionTest(DBTestBase):
    pass


if __name__ == "__main__":
    import unittest
    unittest.main()