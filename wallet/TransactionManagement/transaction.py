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

#from wallet.ChannelManagement.channel import Channel
#from neo.Wallets.Wallet import Wallet


from model.transaction_model import APITransaction,TBLTransaction
from lightwallet.Settings import settings





class TrinityTransaction(object):

    def __init__(self, channel, wallet):
        self.channel = channel
        self.wallet = wallet
        self.transaction = APITransaction(self.channel)

    def transaction_exist(self):
        """

        :return:
        """
        transes = TBLTransaction().list_collections()
        return self.channel in transes

    def read_transaction(self):
        """

        :return:
        """
        return self.transaction.batch_query_transaction({})

    def update_transaction(self, tx_nonce, **kwargs):
        """

        :param tx_nonce:
        :param kwargs:
        :return:
        """
        return self.transaction.update_transaction(tx_nonce,**kwargs)


    @staticmethod
    def sendrawtransaction(raw_data):
        """

        :param raw_data:
        :return:
        """
        return settings.EthClient.SendRawTransaction(raw_data)

    def get_balance(self, tx_nonce):
        tx = self.transaction.query_transaction(tx_nonce)
        balance = tx.get(self.wallet.address)
        return float(balance) if balance else 0


    def get_tx_nonce(self, tx_nonce):
        return self.transaction.query_transaction(tx_nonce)

    def get_latest_nonceid(self):
        trans = self.transaction.batch_query_transaction({})
        return trans[-1].nonce

    def get_transaction_state(self):
        trans = self.transaction.batch_query_transaction({})
        return trans[-1].state

    def realse_transaction(self):
        pass





if __name__== "__main__":
    tx = TrinityTransaction("Mytest","walle")
    TrinityTransaction("Mytest","wallt")
    m = {"test1":1}
    m1 = {"test2":2}
    tx.update_transaction("0",test1=1)
    tx.update_transaction("0",test2=2)
    print(tx.read_transaction())
    tx.update_transaction("1",H=1,x="tt")
    print(dir(tx.read_transaction()))





