import itertools
from eth_utils import decode_hex,\
    is_boolean,\
    is_integer,\
    remove_0x_prefix,\
    to_hex

from eth_utils.crypto import keccak


def to_bytes(primitive=None, hexstr=None, text=None):
    assert_one_val(primitive, hexstr=hexstr, text=text)

    if is_boolean(primitive):
        return b'\x01' if primitive else b'\x00'
    elif isinstance(primitive, bytes):
        return primitive
    elif is_integer(primitive):
        return to_bytes(hexstr=to_hex(primitive))
    elif hexstr is not None:
        if len(hexstr) % 2:
            hexstr = '0x0' + remove_0x_prefix(hexstr)
        return decode_hex(hexstr)
    elif text is not None:
        return text.encode('utf-8')
    raise TypeError("expected an int in first arg, or keyword of hexstr or text")

def sha3(primitive=None, text=None, hexstr=None):
    if isinstance(primitive, (bytes, int, type(None))):
        input_bytes = to_bytes(primitive, hexstr=hexstr, text=text)
        return keccak(input_bytes)

    raise TypeError(
        "You called sha3 with first arg %r and keywords %r. You must call it with one of "
         "these approaches: sha3(text='txt'), sha3(hexstr='0x747874'), "
         "sha3(b'\\x74\\x78\\x74'), or sha3(0x747874)." % (
            primitive,
            {'text': text, 'hexstr': hexstr}
        )
    )

def has_one_val(*args, **kwargs):
    vals = itertools.chain(args, kwargs.values())
    not_nones = list(filter(lambda val: val is not None, vals))
    return len(not_nones) == 1

def assert_one_val(*args, **kwargs):
    if not has_one_val(*args, **kwargs):
        raise TypeError(
            "Exactly one of the passed values can be specified. "
            "Instead, values were: %r, %r" % (args, kwargs)
        )

def get_arg(arguments, index=0, convert_to_int=False, do_parse=False):
    try:
        arg = arguments[index]
        if convert_to_int:
            return int(arg)
        if do_parse:
            return parse_param(arg)
        return arg
    except Exception as e:
        pass
    return None

def get_asset_id(to_send):
    return True