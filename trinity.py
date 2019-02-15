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
import platform
import operator
import os


# version x.y.z
#   This version will have same meaning as Linux
#       x -- Production version with big different feature
#       y -- Odd number means formal version, Even number means development version
#       z -- Count of fixing bugs
__version__ = '0.1.1'
__os_platform__ = platform.system().upper() if platform.system() else 'LINUX'
__running_mode__ = (0 == operator.imod(int(__version__.split('.')[1]), 2))


DATABASE_CONFIG = {
    'authentication': {
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
    },
    'type': os.getenv('DB_TYPE', 'mongodb'),
    'channel': os.getenv('DB_CHANNEL', 'Channel') if __running_mode__ else os.getenv('DB_CHANNEL', 'beta-channel'),
    'trans': os.getenv('DB_TRANS','Transaction') if __running_mode__ else os.getenv('DB_TRANS','beta-trans'),
    'history': os.getenv('DB_HISTORY','History') if __running_mode__ else os.getenv('DB_HISTORY','beta-history'),
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'port': int(os.getenv('DB_PORT', 27017))
}


# local gas settings
GWEI_COEFFICIENT = 20

# Asset Type configuration
SUPPORTED_ASSET_TYPE = {'TNC': '0x65096f2B7A8dc1592479F1911cd2B98dae4d2218'}
IS_SUPPORTED_ASSET_TYPE = lambda asset_type: \
    isinstance(asset_type, str) and \
    (asset_type.upper() in ['TNC'] or (SUPPORTED_ASSET_TYPE['TNC'].__contains__(asset_type.replace('0x', ''))))


# Some configuration related to the logs
LOG_TO_CONSOLE = False
if __os_platform__ in ['LINUX', 'DARWIN']:
    TRINITY_LOG_PATH = os.path.join(r'./temp', r'trinity')
else:
    TRINITY_LOG_PATH = os.getcwd().split(os.sep)[0]+os.sep+r'temp'

# WebSocket server configuration
EVENT_WS_SERVER = {
    'uri': 'ws://47.254.66.224:9000',
    'timeout': None
}

Configure = {
    "alias": "TrinityEthNode",# you can rename your node
    "GatewayURL": "http://localhost:8177",
    "AutoCreate": True, # if the wallet accept the create channel request automatically
    "Channel":{
        "TNC":{"CommitMinDeposit": 1,   # the min commit deposit
               "CommitMaxDeposit": 5000,# the max commit deposit
               "Fee": 0.01 # gateway fee
               }
    },#
    "MaxChannel":100, # the max number to create channel, if 0 , no limited
    "NetAddress":"localhost",
    "RpcListenAddress":"0.0.0.0",
    "NetPort": os.getenv('WALLET_RPC_PORT', "21556"),
    "GatewayTCP":"localhost:8189",
    "AssetType":{
        "TNC": SUPPORTED_ASSET_TYPE['TNC']
    },
    "BlockChain":{
        "EthNetUrl" : "https://ropsten.infura.io"
    },
    "DataBase":{"url": "http://localhost:20554"
                },
    "Version":"v0.2.1",
    "Magic":{
        "Block":5274657374,##binascii.b2a_hex(u"Rtest".encode("utf8"))
        "Trinity":19990331
    }
}