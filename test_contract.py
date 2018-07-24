import asyncio
import binascii

import time

import requests
from eth_account.datastructures import AttributeDict
from eth_utils import keccak
from py_ecc.secp256k1 import privtopub
# from solc import compile_source, compile_files
from ethereum import utils
from ethereum.utils import ecsign, ecrecover_to_pub, privtoaddr, big_endian_to_int, normalize_key, int_to_big_endian, \
    safe_ord, check_checksum, checksum_encode, sha3, encode_int32
from solc import compile_source, compile_files
from web3 import Web3, HTTPProvider
import rlp
from ethereum.transactions import Transaction

w3 = Web3(HTTPProvider('https://ropsten.infura.io/pZc5ZTRYM8wYfRPtoQal'))

# method=binascii.hexlify( w3.sha3(text="Transfer(address,address,uint256)"))
# k="b6a03207128827eaae0d31d97a7a6243de31f2baf99eabd764e33389ecf436fc"
# k = normalize_key(k)
# print(k)
# x, y = privtopub(k)
# print(x,y)
# print(encode_int32(x))
# addr=sha3(encode_int32(x) + encode_int32(y))[12:]


from eth_hash.backends.pysha3 import keccak256

# x=keccak256("f2ee7b0466feb5d6c50d655885c8387ddcf1739929c17bbda3977e330eca895c".encode())
x=keccak256(bytes.fromhex( "f2ee7b0466feb5d6c50d655885c8387ddcf1739929c17bbda3977e330eca895c"))
print(x)

# print(addr)


























