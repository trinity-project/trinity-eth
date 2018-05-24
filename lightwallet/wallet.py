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

# -*- coding:utf-8 -*-

import uuid
import hashlib
import binascii
from lightwallet.accounts import Account
import json
from blockchain.web3client import Client


class Wallet(object):
    """

    """


    def __init__(self, path, passwordKey, create, eth_url=""):

        """

        :param path:
        :param passwordKey:
        :param create:
        """

        self._path = path
        self._accounts = []
        self._keys={}
        self._passwordHash=None
        self.client = Client(eth_url)

        if create:
            self.uuid = uuid.uuid1()
            passwordHash = hashlib.sha256(passwordKey.encode('utf-8')).digest()
            self._passwordHash=binascii.hexlify(passwordHash)
        else:
            walletInfo=self.fromJsonFile(path)
            passwordHash=binascii.unhexlify(walletInfo['password']['passwordHash'])
            if passwordHash is None:
                raise Exception("Password hash not found in database")
            if passwordHash is not None and passwordHash != hashlib.sha256(passwordKey.encode('utf-8')).digest():
                raise Exception("Incorrect Password")
            self._passwordHash = passwordHash
            self._key = Account(json.loads(walletInfo['keystore']))
            self._key.unlock(passwordKey)
            del passwordKey


    @staticmethod
    def Open(path, password):

        return Wallet(path=path, passwordKey=password, create=False)

    @staticmethod
    def Create(path, password):
        """
        Create a new user wallet.

        Args:
            path (str): A path indicating where to create or open the wallet i.e. "/Wallets/mywallet".
            password (str): a 10 characters minimum password to secure the wallet with.

        Returns:
             UserWallet: a UserWallet instance.
        """
        wallet = Wallet(path=path, passwordKey=password, create=True)
        wallet.Name=path.split(".")[0]
        wallet.CreateKeyStore(password)
        wallet.ToJsonFile(path)
        return wallet

    def CreateKeyStore(self, passwordkey, key=None):
        """
        Create a KeyPair and store it encrypted in the database.

        Args:
            private_key (iterable_of_ints): (optional) 32 byte private key.

        Returns:
            KeyPair: a KeyPair instance.
        """
        self._key = Account.new(passwordkey ,key, uuid=self.uuid)
        return self._key

    def ValidatePassword(self, password):
        """
        Validates if the provided password matches with the stored password.

        Args:
            password (string): a password.

        Returns:
            bool: the provided password matches with the stored password.
        """
        return hashlib.sha256(password.encode('utf-8')).digest() == self._passwordHash


    def SignHash(self,message_hash):
        """

        :param tx_data:
        :return:
        """
        return self._key.sign_hash(message_hash)

    def SignTX(self,tx_data: dict):
        """

        :param tx_data:
        :return:
        """
        return self._key.sign_tansaction(tx_data)


    def get_default_address(self):
        return self._accounts[0]["account"].GetAddress()

    def send(self,addresss_to, value, gasLimit=25600):
        tx = self.client.construct_common_tx(self._key.address, addresss_to, value, gasLimit)
        rawdata = self.SignTX(tx)
        return self.client.broadcast(rawdata.rawTransaction)



    def ToJson(self, verbose=False):

        jsn = {}
        jsn['path'] = self._path
        jsn['address'] = self._key.address
        jsn["publickey"] = self._key.pubkey

        return jsn

    def ToJsonFile(self, path):
        jsn={}
        jsn["password"]={"passwordHash":self._passwordHash.decode()}
        jsn["name"]=self.Name
        jsn['keystore'] = self._key.toJson()
        jsn['extra'] ={}

        with open(path,"wb") as f:
            f.write(json.dumps(jsn).encode())
        return None

    def fromJsonFile(self,path):
        with open(path,"rb") as f:
            content=json.loads(f.read().decode())
        return content

    def LoadStoredData(self, key):
        wallet = self.fromJsonFile(self._path)
        return wallet.get("extra").get(key)

    def SaveStoredData(self, key, value):
        wallet_info  = self.fromJsonFile(self._path)
        wallet_info["extra"][key] = value
        with open(self._path,"wb") as f:
            f.write(json.dumps(wallet_info).encode())
