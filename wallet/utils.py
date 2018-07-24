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

from wallet.configure import Configure
from blockchain.interface import get_balance
import re
import hashlib
from log.log import LOG
from lightwallet.Settings import settings


SupportAssetType = ["TNC", "ETH", "GAS"]


def to_aes_key(password):
    """

    :param password:
    :return:
    """

    password_hash = hashlib.sha256(password.encode('utf-8')).digest()
    return hashlib.sha256(password_hash).digest()


def pubkey_to_address(publickey: str):
    """

    :param publickey:
    :return:
    """
    script = b'21' + publickey.encode() + b'ac'
    script_hash = Crypto.ToScriptHash(script)
    address = Crypto.ToAddress(script_hash)
    return address


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
        arg = arguments[index]
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


def check_support_asset_type(asset_type):
    """

    :param asset_type:
    :return:
    """
    if asset_type.upper() in SupportAssetType:
        return True
    else:
        return False


def check_onchain_balance(pubkey, asset_type, depoist):
    """

    :param wallet:
    :param asset_type: eg TNC
    :param depoist:
    :return:
    """
    balance = get_balance(pubkey, asset_type, settings.TNC, settings.TNC_abi)
    if float(depoist) <= float(balance):
        return True
    else:
        return False


def check_max_deposit(deposit):
    maxd = Configure.get("CommitMaxDeposit")
    if maxd is None or str(maxd).upper() == "NULL":
        return True, None
    else:
        try:
            maxd = float(maxd)
        except ValueError as e:
            return False, str(e)

        return float(deposit) <= maxd, maxd


def check_mix_deposit(deposit):
    mixd = Configure.get("CommitMinDeposit")
    if mixd is None or float(mixd) == 0:
        return True, None
    else:
        try:
            mixd = float(mixd)
        except ValueError as e:
            return False, str(e)
        return float(deposit) >= mixd, mixd


def check_deposit(deposit):
    try:
        de = float(deposit)
    except ValueError as e:
        return False, str(e)
    return de > 0, de

def check_partner(wallet, partner):
    """

    :param wallet:
    :param partner:
    :return:
    """
    temp_partner = partner
    if partner.startswith('0x'):
        temp_partner = partner.replace('0x', '')
    p = re.match(r"[0-9|a-f|A-F]{40}@\d+\.\d+\.\d+\.\d+:\d+", temp_partner.strip())
    if p:
        par_pubkey, ip = partner.strip().split("@")
        if par_pubkey == wallet.address:
            return False
        else:
            return True
    else:
        return False


def get_wallet_info(pubkey):
    """

    :param pubkey:
    :return: message dict
    """
    balance = {}
    for i in Configure["AssetType"].keys():
        b = get_balance(pubkey, i.upper(), settings.TNC, settings.TNC)
        balance[i] = b
    message = {
                   "Publickey": pubkey,
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
    if asset_type in ['NEO']:
        LOG.warning('Convert number<{}> to integer for asset<{}> just support integer type transaction.'.format(number, asset_type))
        if isinstance(number, str):
            number = float(number)
        return int(number)

    return number


def convert_float(number, decimals=8):
    return round(float(number),decimals)


def get_magic():
    magic = Configure.get('Magic')
    return magic.get('Block').__str__() + magic.get('Trinity').__str__()


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