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
from .accounts import Account
import json


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

        if create:
            self.uuid = uuid.uuid1()
            passwordHash = hashlib.sha256(passwordKey.encode('utf-8')).digest()
            self._passwordHash=binascii.hexlify(passwordHash)
        else:
            walletInfo=self.fromJsonFile(path)
            passwordHash=binascii.unhexlify(walletInfo["extra"]['passwordHash'])
            if passwordHash is None:
                raise Exception("Password hash not found in database")
            if passwordHash is not None and passwordHash != hashlib.sha256(passwordKey.encode('utf-8')).digest():
                raise Exception("Incorrect Password")
            self._passwordHash = passwordHash
            del passwordKey

    @staticmethod
    def Open(path, password):

        return Nep6Wallet(path=path, passwordKey=password, create=False)

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
        wallet.CreateKeyStore()
        wallet.ToJsonFile(path,password)
        return wallet

    def CreateKeyStore(self, key=None):
        """
        Create a KeyPair and store it encrypted in the database.

        Args:
            private_key (iterable_of_ints): (optional) 32 byte private key.

        Returns:
            KeyPair: a KeyPair instance.
        """
        self._key = Account.new(self._passwordHash,key, uuid=self.uuid)
        return self._key


    @staticmethod
    def ToAddress(scripthash):
        """
        Transform a script hash to an address.

        Args:
            script_hash (UInt160): a bytearray (len 20) representing the public key.

        Returns:
            address (str): the base58check encoded address.
        """
        return scripthash_to_address(scripthash)

    def ToScriptHash(self, address):
        """
        Retrieve the script_hash based from an address.

        Args:
            address (str): a base58 encoded address.

        Raises:
            ValuesError: if an invalid address is supplied or the coin version is incorrect.
            Exception: if the address checksum fails.

        Returns:
            UInt160: script hash.
        """
        data = b58decode(address)
        if len(data) != 25:
            raise ValueError('Not correct Address, wrong length.')
        if data[0] != self.AddressVersion:
            raise ValueError('Not correct Coin Version')

        checksum = Crypto.Default().Hash256(data[:21])[:4]
        if checksum != data[21:]:
            raise Exception('Address format error')
        return UInt160(data=data[1:21])

    def ValidatePassword(self, password):
        """
        Validates if the provided password matches with the stored password.

        Args:
            password (string): a password.

        Returns:
            bool: the provided password matches with the stored password.
        """
        return hashlib.sha256(password.encode('utf-8')).digest() == self._passwordHash

    def GetStandardAddress(self):
        """
        Get the Wallet's default address.

        Raises:
            Exception: if no default contract address is set.

        Returns:
            UInt160: script hash.
        """
        for contract in self._contracts.values():
            if contract.IsStandard:
                return contract.ScriptHash

        raise Exception("Could not find a standard contract address")

    def GetKeys(self):
        """
        Get all keys pairs present in the wallet.

        Returns:
            list: of KeyPairs.
        """
        return [item["account"] for item in self._accounts]

    def Sign(self,tx_data):
        """

        :param tx_data:
        :return:
        """
        privtKey=binascii.hexlify(self._accounts[0]["account"].PrivateKey).decode()
        signature = privtkey_sign(tx_data, privtKey)
        publicKey = privtKey_to_publicKey(privtKey)
        rawData = tx_data + "014140" +signature + "2321" + publicKey + "ac"
        return rawData


    def SignContent(self,tx_data):
        """

        :param tx_data:
        :return:
        """
        privtKey=binascii.hexlify(self._accounts[0]["account"].PrivateKey).decode()
        signature = privtkey_sign(tx_data, privtKey)
        return signature


    def get_default_address(self):
        return self._accounts[0]["account"].GetAddress()

    def send(self,addressFrom,addressTo,amount,assetId):
        res = construct_tx(addressFrom,addressTo,amount,assetId)
        print(res)
        raw_txdata=self.Sign(res["result"]["txData"])
        if send_raw_tx(raw_txdata):
            print("txid: "+res["result"]["txid"])
            return True,res["result"]["txid"]
        return False,res["result"]["txid"]

    def ToJson(self, verbose=False):

        jsn = {}
        jsn['path'] = self._path
        jsn['accounts']=[]
        for item in self._accounts:
            res=get_balance(item["account"].GetAddress())
            tmp_dict={
                "address":item["account"].GetAddress(),
                "pubkey":item["account"].PublicKey.encode_point(True).decode(),
                "assets":{
                    "NEO":res["result"]["neoBalance"],
                    "GAS":res["result"]["gasBalance"],
                    "TNC":res["result"]["tncBalance"]
                }
            }
            jsn['accounts'].append(tmp_dict)
        return jsn

    def ToJsonFile(self, path):
        jsn={}
        jsn["extra"]={"passwordHash":self._passwordHash.decode()}
        jsn["name"]=self.Name
        jsn['keystore'] = self._key
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
