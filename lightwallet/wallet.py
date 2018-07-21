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
from lightwallet.Settings import settings
from ethereum.utils import checksum_encode
from model.history_model import APIHistory
import time
from log import LOG


class Wallet(object):
    """

    """

    def __init__(self, path, passwordKey, create):

        """

        :param path:
        :param passwordKey:
        :param create:
        """

        self._path = path
        self._accounts = []
        self._keys={}
        self._passwordHash=None
        self.locked = False
        self.name = path.split(".")[0]
        self.history = APIHistory()

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

    @property
    def address(self):
        """

        :return:
        """

        if self._key:
            return self._key.address
        else:
            return None

    @property
    def pubkey(self):
        """

        :return:
        """
        if self._key:
            return self._key.pubkey_safe
        else:
            return None


    def get_default_address(self):
        """

        :return:
        """
        return self._accounts[0]["account"].GetAddress()

    def send_eth(self,address_to, value, gasLimit=25600):
        """

        :param addresss_to:
        :param value:
        :param gasLimit:
        :return:
        """

        addresss_to = checksum_encode(address_to)
        tx = settings.EthClient.construct_common_tx(self._key.address, addresss_to, value, gasLimit)
        rawdata = self.SignTX(tx)
        return self._sendraw_and_recordhistory(rawdata=rawdata,asset_id="Eth", sendto=address_to, value=value)


    def _sendraw_and_recordhistory(self, rawdata,asset_id, sendto, value):
        try:
            tx_id = self.SendRawTransaction(rawdata.rawTransaction)

        except Exception as e:
            raise Exception(e)

        tx_id = binascii.hexlify(tx_id).decode()
        try:
            self.record_history(tx_id=tx_id, asset_id=asset_id, sendto=sendto, value=value)
        except Exception as e:
            LOG.error("Record history error {}".format(e))

        return tx_id


    def send_erc20(self, asset, address_to, value, gasLimit=25600, gasprice=None):
        """

        :param asset:
        :param address_to:
        :param value:
        :param gasLimit:
        :param gasprice:
        :return:
        """

        conract_address, abi, decimals = self.get_contract(asset)

        if not conract_address or not abi or not decimals:
            raise Exception("can not get asset %s info" %asset)

        contract_instance = settings.EthClient.get_contract_instance(conract_address,
                                                       abi)
        address_to = checksum_encode(address_to)
        tx = settings.EthClient.construct_erc20_tx(contract_instance, self._key.address,
                                                   int(value*10*decimals), gasLimit, gasprice)
        rawdata = self.SignTX(tx)

        asset = "{}({})".format(asset, conract_address)
        return self._sendraw_and_recordhistory(rawdata, asset, address_to, value)

    def get_contract(self, asset):
        """

        :param asset:
        :return:
        """
        if asset.upper() == "TNC":
            return settings.TNC, settings.TNCabi, 8
        else:
            return self.search_asset(asset)

    def search_asset(self, asset):
        """
        todo
        :param asset:
        :return:
        """
        return None, None, None

    def ToJson(self, verbose=False):
        """

        :param verbose:
        :return:
        """

        jsn = {}
        jsn['path'] = self._path
        jsn['address'] = self._key.address
        jsn["publickey"] = self._key.pubkey
        jsn["ETH"] = self.eth_balance
        jsn["TNC"] = self.tnc_balance

        return jsn

    @property
    def eth_balance(self):
        """

        :return:
        """

        return settings.EthClient.get_balance_of_eth(self._key.address)

    @property
    def tnc_balance(self):
        """

        :return:
        """
        return settings.EthClient.get_balance_of_erc20(settings.TNC, settings.TNCabi,
                                                       self._key.address)

    def ToJsonFile(self, path):
        """

        :param path:
        :return:
        """

        jsn={}
        jsn["password"]={"passwordHash":self._passwordHash.decode()}
        jsn["name"]=self.name
        jsn['keystore'] = self._key.toJson()
        jsn['extra'] ={}

        with open(path,"wb") as f:
            f.write(json.dumps(jsn).encode())
        return None

    def fromJsonFile(self,path):
        """

        :param path:
        :return:
        """

        with open(path,"rb") as f:
            content=json.loads(f.read().decode())
        return content

    def LoadStoredData(self, key):
        """

        :param key:
        :return:
        """

        wallet = self.fromJsonFile(self._path)
        return wallet.get("extra").get(key)

    def SaveStoredData(self, key, value):
        """

        :param key:
        :param value:
        :return:
        """
        wallet_info  = self.fromJsonFile(self._path)
        wallet_info["extra"][key] = value
        with open(self._path,"wb") as f:
            f.write(json.dumps(wallet_info).encode())

    def SendRawTransaction(self, rawdata):
        """

        :param rawdata:
        :return:
        """
        return settings.EthClient.broadcast(rawdata)

    def record_history(self, tx_id,asset_id, sendto, value):
        """

        :param asset_id:
        :param sendto:
        :param value:
        :return:
        """


        self.history.set_history_collection(self.address)
        his = {"tx_id":tx_id,
               "asset":asset_id,
               "sender":self.address,
               "receiver":sendto,
               "value":value,
               "block":"null",
               "state":"waiting"}
        return self.history.add_history(**his)

    def update_history(self, tx_id, block, state):
        """

        :param tx_id:
        :param block:
        :param state:
        :return:
        """
        self.history.set_history_collection(self.address)

        return self.history.update_history(tx_id,block=block,state=state)

    def query_history(self,**kwargs):
        """

        :param kwargs:
        :return:
        """
        self.history.set_history_collection(self.address)
        if not kwargs:
            return self.history.batch_query_history({})
        else:
            return self.history.batch_query_history(kwargs)





