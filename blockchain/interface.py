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
from .web3client import Client
from wallet.configure import Configure
from log import LOG
from tokenconf import TokenConfigure


AssetType=Configure["AssetType"]


NetUrl = Configure['BlockChain']['EthNetUrl']

EthClient = Client(NetUrl)


def send_raw(raw_data):
    return EthClient.broadcast(raw_data)

def get_block_count():
    return EthClient.get_block_count()


def get_block(index):
    return EthClient.get_block(index)


def get_balance(address, asset_type):
    """

    :param address:
    :param asset_type: asset symbol
    :return:
    """
    if asset_type.upper() == "ETH":
        try:
            return EthClient.get_balance_of_eth(address)
        except Exception as e:
            LOG.error(e)
            return 0
    else:
        try:
            contract_address = TokenConfigure.get(asset_type.upper()).get("ContractAddress")
            abi = Configure.get(asset_type.upper()).get("ABI")
            contract = EthClient.get_contract_instance(contract_address, abi)
            return EthClient.get_balance_of_erc20(contract, address)
        except Exception as e:
            LOG.error(e)
            return 0


def get_application_log(filter_id):
    return EthClient.get_fitler_log(filter_id)


def check_vmstate(filter_id):
    pass #ToDo


def hex2interger(input):
    tmp_list=[]
    for i in range(0,len(input),2):
        tmp_list.append(input[i:i+2])
    hex_str="".join(list(reversed(tmp_list)))
    output=int(hex_str,16)/100000000

    return output