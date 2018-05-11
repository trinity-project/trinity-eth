from functools import total_ordering
import json
import os
from random import SystemRandom
import shutil
from uuid import UUID
from ethereum.tools import keys
from ethereum.slogging import get_logger
from ethereum.utils import privtopub  # this is different  than the one used in devp2p.crypto
from ethereum.utils import sha3, is_string, encode_hex, remove_0x_head, to_string
from rlp.utils import decode_hex
import bitcoin



log = get_logger('accounts')

DEFAULT_COINBASE = decode_hex('de0b295669a9fd93d5f28d9ec85e40f4cb697bae')

random = SystemRandom()


def mk_privkey(seed):
    return sha3(seed)


def mk_random_privkey():
    k = hex(random.getrandbits(256))[2:-1].zfill(64)
    assert len(k) == 64
    return decode_hex(k)


class Account(object):
    """

    """

    def __init__(self, keystore, password=None, path=None):
        self.keystore = keystore
        try:
            self._address = decode_hex(self.keystore['address'])
        except KeyError:
            self._address = None
        self.locked = True
        if password is not None:
            self.unlock(password)
        if path is not None:
            self.path = os.path.abspath(path)
        else:
            self.path = None

    @classmethod
    def new(cls, password, key=None, uuid=None, path=None):
        """

        :param password:
        :param key:
        :param uuid:
        :param path:
        :return:
        """
        if key is None:
            key = mk_random_privkey()

        # [NOTE]: key and password should be bytes
        if not is_string(key):
            key = to_string(key)
        if not is_string(password):
            password = to_string(password)

        keystore = keys.make_keystore_json(key, password)
        keystore['id'] = uuid
        return Account(keystore, password, path)

    @classmethod
    def load(cls, path, password=None):
        """
        :param path:
        :param password:
        :return:
        """
        with open(path) as f:
            keystore = json.load(f)
        if not keys.check_keystore_json(keystore):
            raise ValueError('Invalid keystore file')
        return Account(keystore, password, path=path)

    def toJson(self, include_address=True, include_id=True):
        """

        :param include_address:
        :param include_id:
        :return:
        """

        d = {}
        d['crypto'] = self.keystore['crypto']
        d['version'] = self.keystore['version']
        if include_address and self.address is not None:
            d['address'] = self.address
        if include_id and self.uuid is not None:
            d['id'] = str(self.uuid)
        return d

    def dump(self, include_address=True, include_id=True):
        """

        :param include_address:
        :param include_id:
        :return:
        """
        return json.dumps(self.toJson(include_address, include_id))

    def save(self, include_address=True, include_id=True):
        """

        :return:
        """
        if self.path:
            with open(self.path) as f:
                json.dump(f, self.toJson(include_address, include_id))
        else:
            raise Exception("No path given")

    def unlock(self, password):
        """Unlock the account with a password.

        If the account is already unlocked, nothing happens, even if the password is wrong.

        :raises: :exc:`ValueError` (originating in ethereum.keys) if the password is wrong (and the
                 account is locked)
        """
        if self.locked:
            self._privkey = keys.decode_keystore_json(self.keystore, password)
            self.locked = False
            self.address  # get address such that it stays accessible after a subsequent lock

    def lock(self):
        """

        :return:
        """
        self._privkey = None
        self.locked = True

    @property
    def privkey(self):
        """The account's private key or `None` if the account is locked"""
        if not self.locked:
            return self._privkey
        else:
            return None

    @property
    def pubkey(self):
        """The account's public key or `None` if the account is locked"""
        if not self.locked:
            return privtopub(self.privkey)
        else:
            return None

    @property
    def address(self):
        """

        :return:
        """
        if self._address:
            pass
        elif 'address' in self.keystore:
            self._address = decode_hex(self.keystore['address'])
        elif not self.locked:
            self._address = keys.privtoaddr(self.privkey)
        else:
            return None
        return encode_hex(self._address)

    @property
    def uuid(self):
        """

        """
        try:
            return self.keystore['id']
        except KeyError:
            return None

    @uuid.setter
    def uuid(self, value):
        """

        :param value: if value is None, remove it
        :return:
        """
        if value is not None:
            self.keystore['id'] = value
        elif 'id' in self.keystore:
            self.keystore.pop('id')

    def sign_tx(self, tx):
        """

        :param tx:
        :return:
        """
        if self.privkey:
            log.info('signing tx', tx=tx, account=self)
            tx.sign(self.privkey)
        else:
            raise ValueError('Locked account cannot sign tx')

    def __repr__(self):
        if self.address is not None:
            address = encode_hex(self.address)
        else:
            address = '?'
        return '<Account(address={address}, id={id})>'.format(address=address, id=self.uuid)




@total_ordering
class MinType(object):
    """ Return Min value for sorting comparison

    This class is used for comparing unorderded types. e.g., NoneType
    """

    def __le__(self, other):
        return True

    def __eq__(self, other):
        return (self is other)


def privtoaddr(x):
    if len(x) > 32:
        x = decode_hex(x)
    return sha3(bitcoin.privtopub(x)[1:])[12:]






if __name__ == "__main__":
    account = Account.new("mytest",path="./test")
    print(account.pubkey)
    print(encode_hex(bitcoin.privtopub(account.privkey)))
    print(encode_hex(account.privkey))
    print(account.address)
    print(account.dump())
