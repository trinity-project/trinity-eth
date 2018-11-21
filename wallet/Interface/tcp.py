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


from twisted.internet import reactor, protocol
from trinity import Configure
from wallet.Interface.gate_way import join_gateway,get_gw_bytes_encoding
from wallet.Interface.rpc_interface import CurrentLiveWallet
from common.log import LOG


class GatwayClientProtocol(protocol.Protocol):
    """
    Once connected, send a message
    """
    printlog = True

    def connectionMade(self):
        """
        once the connection made send the gateway info
        """

        message = {
                   "MessageType": "RegisterKeepAlive",
                   "Ip":          "{}:{}".format(Configure.get("NetAddress"),Configure.get("NetPort"))
                  }
        self.transport.write(encode_bytes(message))
        if CurrentLiveWallet.Wallet:
            join_gateway(CurrentLiveWallet.Wallet)
        else:
            pass
        print("Connect the Gateway")
        GatwayClientProtocol.printlog = True

    def datasend(self, message):
        """
        sendate
        :param message:
        :return:
        """
        self.transport.write(message.encode())



class GatwayClientFactory(protocol.ClientFactory):
    """

    """

    protocol = GatwayClientProtocol


    def _handle_connection_lose(self, connector):
        connector.connect()
        GatwayClientProtocol.printlog=False


    def clientConnectionLost(self, connector, reason):
        """
        connection lost

        :param connector:
        :param reason:
        :return:
        """
        if GatwayClientProtocol.printlog:
            print('Lost Gateway')
            LOG.error(reason)
        self._handle_connection_lose(connector)



    def clientConnectionFailed(self, connector, reason):
        """
        connection failed
        :param connector:
        :param reason:
        :return:
        """

        if GatwayClientProtocol.printlog:
            print('Can Not connect Gateway, Please Check the gateway')
            LOG.error(reason)
        self._handle_connection_lose(connector)



def encode_bytes(data):
    """
    encode the data as gateway used
    :param data:
    :return:
    """
    import json
    import struct

    cg_bytes_encoding = get_gw_bytes_encoding()
    if type(data) != str:
        data = json.dumps(data)
    # data = _add_end_mark(data)
    version = 0x000001
    cmd = 0x000065
    bdata = data.encode(cg_bytes_encoding)
    header = [version, len(bdata), cmd]
    header_pack = struct.pack("!3I", *header)
    return header_pack + bdata



if __name__ == '__main__':
    f = GatwayClientFactory()
    reactor.connectTCP("localhost", 10000, f)
    reactor.run()