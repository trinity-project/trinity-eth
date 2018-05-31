from functools import wraps
from enum import Enum

import binascii
import requests
from ethereum import utils
from ethereum.utils import privtoaddr, normalize_key, ecsign
from flask import jsonify



def response_wrap(func):
    @wraps(func)
    def wrapper():
        response=func()
        return jsonify(response)
    return wrapper


class ASSET_TYPE(Enum):
    TNC=2443
    NEO=1376
    GAS=1785
    ETH=1027

def get_price_from_coincapmarket(asset_type):
    coincapmarket_api="https://api.coinmarketcap.com/v2/ticker/{0}/?convert=CNY".format(asset_type)
    print(coincapmarket_api)
    res=requests.get(coincapmarket_api).json()
    return res.get("data").get("quotes").get("CNY").get("price")
# fbadf8a0794e71f425c2b0b025fa3d2543d81792d8e07e8aaeba99a5d0e77273
key="095e53c9c20e23fd01eaad953c01da9e9d3ed9bebcfed8e5b2c2fce94037d963"
# key="fbadf8a0794e71f425c2b0b025fa3d2543d81792d8e07e8aaeba99a5d0e77273"
#
#
# key = normalize_key(key)
# addr=privtoaddr(key)
# print("key:",key)
# import binascii
# print("addr:",binascii.hexlify( addr))
# pass


before_hash=utils.sha3(binascii.unhexlify("a84584b2590ccd7453ffe65fa3bbf55b600153bbac2af75f0a87b4ad55a96da4".encode()))
before_hash=binascii.hexlify(before_hash)
v,r,s=ecsign(before_hash,normalize_key(key))
pass

0x75381f959c48214b960b4a2ce8a6b878b66ecd12
