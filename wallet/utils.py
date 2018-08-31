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

from trinity import Configure
from blockchain.interface import get_balance
import re
import hashlib
from common.log import LOG
from common.number import TrinityNumber
from lightwallet.Settings import settings
import datetime
import requests


class SupportAssetType(object):
    """

    """
    SupportAssetType = ["TNC"]

    @classmethod
    def get_asset(cls, asset_type):
        if asset_type.upper() == "ETH":
            return "ETH", None
        elif asset_type.upper() == "TNC":
            return settings.TNC, settings.TNC_abi
        else:
            return None , None # ToDo

    @classmethod
    def get_asset_decimals(cls, asset_type):
        if asset_type.upper() == "ETH":
            return 18
        elif asset_type.upper() == "TNC":
            return 8
        else:
            return None # ToDo


class DepositAuth(object):
    """
    """
    DefaultDeposit = 5000
    LastGetTime = None
    DateSource = "https://api.coinmarketcap.com/v2/ticker/2443/?convert=USD"

    @classmethod
    def query_deposit(cls):
        """

        :return:
        """
        try:
            result = requests.get(cls.DateSource)
            if not result.ok:
                return None
            return result.json()["data"]
        except Exception as e:
            LOG.error(str(e))
            return None

    @classmethod
    def caculate_depositusd(cls):
        """

        :return:
        """
        return 800*1.03**(abs((datetime.date.today()-datetime.date(2018,1,15)).days)//365)

    @classmethod
    def caculate_deposit(cls):
        """

        :return:
        """

        deposit_info = cls.query_deposit()
        try:
            tnc_price_usdt = deposit_info["quotes"]["USD"]["price"]
            deposit_limit = int(cls.caculate_depositusd()/tnc_price_usdt)
            return deposit_limit if deposit_limit >0 else 1
        except Exception as e:
            LOG.error(str(e))
            return cls.DefaultDeposit


    @classmethod
    def deposit_limit(cls):
        """

        :return:
        """

        deposit = cls.caculate_deposit()
        cls.DefaultDeposit = deposit
        cls.LastGetTime = datetime.date.today()

        return cls.DefaultDeposit


def to_aes_key(password):
    """

    :param password:
    :return:
    """

    password_hash = hashlib.sha256(password.encode('utf-8')).digest()
    return hashlib.sha256(password_hash).digest()



# def pubkey_to_address(publickey: str):
#     """
#
#     :param publickey:
#     :return:
#     """
#     script = b'21' + publickey.encode() + b'ac'
#     script_hash = Crypto.ToScriptHash(script)
#     address = Crypto.ToAddress(script_hash)
#     return address


def sign(wallet, context):
    """

    :param wallet:
    :param context:
    :return:
    """
    res = wallet.SignContent(context)
    return res


def get_arg(arguments, index=0, convert_to_int=False):
    """

    :param arguments:
    :param index:
    :param convert_to_int:
    :param do_parse:
    :return:
    """

    try:
        arg = arguments[index].strip()
        if convert_to_int:
            return int(arg)
        return arg
    except Exception as e:
        pass
    return None


def get_asset_type_name(asset_type):
    """

    :param asset_type:
    :return:
    """
    asset= Configure.get("AssetType")
    for key, value in asset.items():
        if value.replace("0x","") == asset_type.replace("0x",""):
            return key
        else:
            continue
    return None


def get_asset_type_id(asset_name):
    """

    :param asset_name:
    :return:
    """
    return Configure.get("AssetType").get(asset_name.upper())

def get_support_asset():
    return SupportAssetType.SupportAssetType

def check_support_asset_type(asset_type):
    """

    :param asset_type:
    :return:
    """
    if asset_type:
        if asset_type.upper() in SupportAssetType.SupportAssetType:
            return True
        else:
            return False
    else:
        return False


def check_onchain_balance(pubkey, asset_type, deposit):
    """

    :param wallet:
    :param asset_type: eg TNC
    :param deposit:
    :return:
    """
    asset_symbol, asset_abi = SupportAssetType.get_asset(asset_type)
    balance = get_balance(pubkey, asset_type, asset_symbol, asset_abi)
    balance = TrinityNumber(str(balance)).number
    if balance is not None and deposit <= balance:
        return True
    else:
        return False


def is_correct_uri(uri):
    """

    :param uri:
    :return:
    """
    uri = uri if not uri.startswith('0x') else uri.replace('0x', '')
    return re.match(r"[0-9|a-f|A-F]{40}@\d+\.\d+\.\d+\.\d+:\d+", uri.strip()) is not None


def check_partner(wallet, partner):
    """

    :param wallet:
    :param partner:
    :return:
    """

    if is_correct_uri(partner):
        par_pubkey, ip = partner.strip().split("@")
        if par_pubkey == wallet.address:
            return False
        else:
            return True
    else:
        return False


def get_wallet_info(wallet):
    """

    :param wallet:
    :return: message dict
    """
    balance = {}
    # for i in Configure["AssetType"].keys():
    #     b = get_balance(wallet.address, i.upper(), settings.TNC, settings.TNC)
    #     balance[i] = b
    balance["ETH"] = wallet.eth_balance
    balance["TNC"] = wallet.tnc_balance
    message = {
                   "Publickey": wallet.address,
                    "alias": Configure["alias"],
                    "AutoCreate": Configure["AutoCreate"],
                    "Ip": "{}:{}".format(Configure.get("NetAddress"),
                                         Configure.get("NetPort")),
                    "MaxChannel": Configure["MaxChannel"],
                   "Channel": Configure["Channel"],
                   "Balance": balance,
               }
    return message


def convert_number_auto(asset_type, number: int or float or str):
    if isinstance(number, str):
        number = float(number)
    return int(number)


def convert_float(number, asset_type="TNC"):
    """

    :param number:
    :param asset_type:
    :return:
    """
    decimals = SupportAssetType.get_asset_decimals(asset_type)
    if decimals is None:
        raise Exception("NoSupportAsset")
    return round(float(number),decimals)


def check_float_decimals(number, asset_type):
    """

    :param number:
    :param asset_type:
    :return:
    """
    decimals = SupportAssetType.get_asset_decimals(asset_type)
    if decimals is None:
        return False
    num = str(number).split(".")
    if len(num) ==1:
        return True
    elif len(num) == 0:
        return False
    elif len(num[1])> decimals:
        return False
    return True


def get_magic():
    """
    get the configured magic
    :return:
    """
    magic = Configure.get('Magic')
    return magic.get('Block').__str__() + magic.get('Trinity').__str__()


def is_valid_deposit(asset_type, deposit, spv_wallet=False):
    """

    :param asset_type:
    :param deposit:
    :param spv_wallet:
    :return:
    """
    if len(asset_type) >10:
        asset_type = get_asset_type_name(asset_type)
    else:
        asset_type = asset_type.upper()

    if not asset_type:
        LOG.error('Must specified the asset type. Current value is None')
        return False

    if spv_wallet:
        try:
            max_deposit_configure = Configure.get("Channel").get(asset_type).get("CommitMaxDeposit")
        except Exception as e:
            LOG.warn(str(e))
            max_deposit_configure = 0
        try:
            min_deposit_configure = Configure.get("Channel").get(asset_type.upper()).get("CommitMinDeposit")
        except Exception as e:
            LOG.warn(str(e))
            min_deposit_configure = 0

        max_deposit = float(max_deposit_configure)
        min_deposit = float(min_deposit_configure)

        if min_deposit > 0 and max_deposit > 0:
            return min_deposit <= deposit <= max_deposit, None

        elif 0 >= min_deposit:
            LOG.warn('CommitMinDeposit is set as an illegal value<{}>.'.format(str(min_deposit)))
            return deposit <= max_deposit, None
        elif 0 >= max_deposit:
            LOG.warn('CommitMaxDeposit is set as an illegal value<{}>.'.format(str(max_deposit)))
            return deposit >= min_deposit, None
    else:
        if asset_type == "TNC":
            deposit_l = DepositAuth.deposit_limit()
            if deposit <= deposit_l:
                return False, "Node wallet channel deposit should larger than {}, " \
                              "but now is {}".format(str(deposit_l),str(deposit))
        return True, None





if __name__ == "__main__":
    # print(pubkey_to_address("03a6fcaac0e13dfbd1dd48a964f92b8450c0c81c28ce508107bc47ddc511d60e75"))
    # print(Crypto.Hash160("02cebf1fbde4786f031d6aa0eaca2f5acd9627f54ff1c0510a18839946397d3633".encode()))
    import time
    print(time.time())
    r=convert_float(1.1234567890)
    print(type(r))
    print(time.time())
    float("1.234567890")
    print(time.time())