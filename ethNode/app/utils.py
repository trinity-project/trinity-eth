from functools import wraps
from enum import Enum

import requests
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