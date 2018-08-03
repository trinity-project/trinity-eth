#!/usr/bin/env python3

import os
import sys
pythonpath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(pythonpath)

import argparse
import json
import traceback
import signal
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import print_tokens
from prompt_toolkit.token import Token
from twisted.internet import reactor, endpoints, protocol
from log import LOG
from lightwallet.Settings import settings
from wallet.utils import get_arg, \
    get_asset_type_name,\
    check_onchain_balance,\
    check_support_asset_type,\
    check_partner, \
    is_valid_deposit
from wallet.Interface.rpc_interface import RpcInteraceApi,CurrentLiveWallet
from twisted.web.server import Site
from lightwallet.prompt import PromptInterface
from wallet.ChannelManagement.channel import create_channel, \
    filter_channel_via_address,\
    get_channel_via_address,\
    chose_channel,\
    close_channel,\
    udpate_channel_when_setup
from wallet.ChannelManagement import channel as ch
from wallet.TransactionManagement import message as mg
from wallet.TransactionManagement import transaction as trinitytx
from wallet.Interface.rpc_interface import MessageList
import time
from model.base_enum import EnumChannelState
from wallet.Interface import gate_way
from wallet.configure import Configure
from blockchain.interface import get_block_count
from blockchain.event import event_init_wallet
from functools import reduce
from blockchain.monior import monitorblock,EventMonitor
from wallet.TransactionManagement.payment import Payment
import requests
import qrcode_terminal
from wallet.configure import Configure


GateWayIP = Configure.get("GatewayIP")
Version = Configure.get("Version")


class UserPromptInterface(PromptInterface):
    Channel = False

    def __init__(self):
        super().__init__()
        self.user_commands = ["channel enable",
                              "channel create {partner} {asset_type} {deposit}",
                              "channel tx {payment_link}/{receiver} {asset_type} {count}",
                              "channel close {channel}",
                              "channel peer",
                              "channel payment {asset}, {count}, [{comments}]",
                              "channel qrcode {on/off}",
                              "channel trans",
                              "channel show uri",
							  "channel show trans_history {channel}",
                              "channel depoist_limit",
                              "contract approve {count}",
                              "contract check-approved"
                              ]
        self.commands.extend(self.user_commands)
        self.qrcode = False

    def get_address(self):
        """

        :return:
        """
        return self.Wallet.address


    def run(self):
        """
        :return:
        """

        tokens = [(Token.Neo, 'TRINITY'), (Token.Default, ' cli. Type '),
                  (Token.Command, "'help' "), (Token.Default, 'to get started')]

        print_tokens(tokens,self.token_style)
        print("\n")


        while self.go_on:
            try:
                result = prompt("trinity>",
                                history=self.history,
                                get_bottom_toolbar_tokens=self.get_bottom_toolbar,
                                style=self.token_style,
                                refresh_interval=3
                                )
            except EOFError:
                return self.quit()
            except KeyboardInterrupt:
                self.quit()
                continue

            try:
                command, arguments = self.parse_result(result)

                if command is not None and len(command) > 0:
                    command = command.lower()

                    if command == 'quit' or command == 'exit':
                        self.quit()
                    elif command == 'help':
                        self.help()
                    elif command == 'wallet':
                        self.show_wallet(arguments)
                    elif command is None:
                        print('please specify a command')
                    elif command == 'create':
                        self.do_create(arguments)
                    elif command == 'close':
                        self.do_close_wallet()
                    elif command == 'open':
                        self.do_open(arguments)
                    elif command == 'export':
                        self.do_export(arguments)
                    elif command == 'send':
                        self.do_send(arguments)
                    elif command == 'tx':
                        self.show_tx(arguments)
                    elif command == 'channel':
                        self.do_channel(arguments)
                    elif command == "faucet":
                        self.do_faucet()
                    elif command == 'contract':
                        self.do_contract(arguments)
                    else:
                        print("command %s not found" % command)

            except Exception as e:

                print("could not execute command: %s " % e)
                traceback.print_stack()
                traceback.print_exc()

    def get_bottom_toolbar(self, cli=None):
        out = []
        try:
            out = [
                (Token.Command, "[%s]" % settings.NET_NAME),
                (Token.Default, str(EventMonitor.get_wallet_block_height())),
                (Token.Command, '/'),
                (Token.Default, str(EventMonitor.get_block_height()))]

        except Exception as e:
            pass
        return out

    #faucet for test tnc
    def do_faucet(self):
        if not self.Wallet:
            print("Please Open The Wallet First")
            return
        print(self.Wallet.address)
        request = {
                "jsonrpc": "2.0",
                "method": "transferTnc",
                "params": ["AGgZna4kbTXPm16yYZyG6RyrQz2Sqotno6",self.Wallet.address],
                "id": 1
                }
        result = requests.post(url=Configure['BlockChain']['NeoUrlEnhance'], json=request)
        txid = result.json().get("result")
        if txid:
            print(txid)
        else:
            print(result.json())
        return

    def retry_channel_enable(self):
        for i in range(30):
            enable = self.enable_channel()
            if enable:
                return True
            else:
                sys.stdout.write("Wait connect to gateway...{}...\r".format(i))
                time.sleep(0.2)
        return self._channel_noopen()

    def do_open(self, arguments):
        super().do_open(arguments)
        if self.Wallet:
            event_init_wallet(self.Wallet.address)
            CurrentLiveWallet.update_current_wallet(self.Wallet)
            self.Wallet.BlockHeight = self.Wallet.LoadStoredData("BlockHeight")
            EventMonitor.start_monitor(self.Wallet)
            result = self.retry_channel_enable()
            if result:
                udpate_channel_when_setup(self.Wallet.url)

    def do_create(self, arguments):
        super().do_create(arguments)
        if self.Wallet:
            CurrentLiveWallet.update_current_wallet(self.Wallet)
            blockheight = get_block_count()
            self.Wallet.BlockHeight = blockheight
            self.Wallet.SaveStoredData("BlockHeight", blockheight)
            EventMonitor.start_monitor(self.Wallet)
            self.retry_channel_enable()

    def do_close_wallet(self):
        if self.Wallet:
            self.Wallet.SaveStoredData("BlockHeight", self.Wallet.BlockHeight)
            try:
                gate_way.close_wallet()
            except Exception as e:
                LOG.error(e)
        super().do_close_wallet()

    def quit(self):
        print('Shutting down. This may take about 15 sec to sync the block info')
        self.go_on = False
        EventMonitor.stop_monitor()
        self.do_close_wallet()
        CurrentLiveWallet.update_current_wallet(None)
        reactor.stop()

    def enable_channel(self):
        try:
            result = gate_way.join_gateway(self.Wallet.address).get("result")
            if result:
                self.Wallet.url = json.loads(result).get("MessageBody").get("Url")

                try:
                    spv = json.loads(result).get("MessageBody").get("Spv")
                    spv_port = spv.strip().split(":")[1]
                except:
                    spv_port = "8766"
                gate_way.GatewayInfo.update_spv_port(spv_port)
                self.Channel = True
                print("Channel Function Enabled")
                return True
        except requests.exceptions.ConnectionError:
            pass
        return False

    def do_contract(self, arguments):
        if not self.Wallet:
            print("Please open a wallet")
            return

        command = get_arg(arguments)
        asset_command = [i.split()[1] for i in self.user_commands]
        if command not in asset_command:
            print("no support command, please check the help")
            self.help()
            return

        if command == 'approve':
            deposit = get_arg(arguments, 1)
            try:
                ch.Channel.approve(self.Wallet.address, deposit, self.Wallet._key.private_key_string)
            except Exception as error:
                print('Error to approved asset to contract. {}'.format(error))

        elif command == "check-approved":
            try:
                result = ch.Channel.get_approved_asset(self.Wallet.address)
            except Exception as error:
                result = 0
            else:
                if not result:
                    result = 0
                print('Has approved {}'.format(result))

        return

    def do_channel(self,arguments):
        if not self.Wallet:
            print("Please open a wallet")
            return

        command = get_arg(arguments)
        channel_command = [i.split()[1] for i in self.user_commands]
        if command not in channel_command:
            print("no support command, please check the help")
            self.help()
            return

        if command == 'create':
            if not self.Channel:
                self._channel_noopen()
            assert 5 >= len(arguments) >= 4, 'Length of arguments should be 4 or 5'
            if not self.Wallet:
                raise Exception("Please Open The Wallet First")
            partner = get_arg(arguments, 1)
            asset_type = get_arg(arguments, 2)
            asset_type =asset_type.upper() if check_support_asset_type(asset_type) else None
            if not asset_type:
                print("No support asset type %s" %asset_type)
                return None
            deposit = float(get_arg(arguments, 3).strip())
            partner_deposit = float(get_arg(arguments, 4).strip()) if get_arg(arguments, 4) else deposit

            if not check_onchain_balance(self.Wallet.address, asset_type, deposit):
                print("Now the balance on-chain is less than the deposit.")
                return None

            if not check_partner(self.Wallet, partner):
                print("Partner URI is not correct, Please check the partner uri")
                return None

            if not check_onchain_balance(partner.strip().split("@")[0], asset_type, deposit):
                print("Partner balance on chain is less than the deposit")
                return None

            create_channel(self.Wallet.url, partner, asset_type, deposit, partner_deposit, wallet=self.Wallet)

        elif command == "enable":
            if not self.enable_channel():
                self._channel_noopen()

        elif command == "tx":
            if not self.Channel:
                self._channel_noopen()
            argument1 = get_arg(arguments,1)
            if argument1 is None:
                self.help()
                return None
            if len(argument1) > 88:
                # payment code
                result, info = Payment.decode_payment_code(argument1)
                if result:
                    info = json.loads(info)
                    receiver = info.get("uri")
                    hr = info.get("hr")
                    asset_type = info.get("asset_type")
                    asset_type = get_asset_type_name(asset_type)
                    count = info.get("count")
                    comments = info.get("comments")
                else:
                    print("The payment code is not correct")
                    return
            else:
                receiver = get_arg(arguments, 1)
                asset_type = get_arg(arguments, 2)
                count = get_arg(arguments, 3)
                hr = None
                if not receiver or not asset_type or not count:
                    self.help()
                    return None

                asset_type = asset_type.upper() if check_support_asset_type(asset_type) else None
                if not asset_type:
                    print("No support asset type %s" % asset_type)
                    return None
            ch.Channel(self.Wallet.url, receiver).transfer(self.Wallet.url, receiver, asset_type, count, hr, self.Wallet)

            # receiverpubkey, receiverip= receiver.split("@")
            channels = filter_channel_via_address(self.Wallet.url,receiver, EnumChannelState.OPENED.name)
            # LOG.debug("Channels {}".format(str(channels)))
            # ch = chose_channel(channels,self.Wallet.url.split("@")[0].strip(), count, asset_type)
            # if ch:
            #     channel_name = ch.channel
            # else:
            #     channel_name =None
            # gate_way_ip = self.Wallet.url.split("@")[1].strip()
            #
            # if channel_name:
            #     tx_nonce = trinitytx.TrinityTransaction(channel_name, self.Wallet).get_latest_nonceid()
            #     mg.RsmcMessage.create(channel_name,self.Wallet,self.Wallet.pubkey,
            #                           receiverpubkey, float(count), receiverip, gate_way_ip, str(tx_nonce+1),
            #                           asset_type=asset_type, comments=hr)
            # else:
            #     message = {"MessageType":"GetRouterInfo",
            #                "Sender":self.Wallet.url,
            #                 "Receiver": receiver,
            #                "MessageBody":{
            #                    "AssetType":asset_type,
            #                    "Value":count
            #                    }
            #                }
            #     result = gate_way.get_router_info(message)
            #     routerinfo = json.loads(result.get("result"))
            #     router=routerinfo.get("RouterInfo")
            #     if router:
            #         if not hr:
            #             print("No hr in payments")
            #             return
            #         r = router.get("FullPath")
            #         LOG.info("Get Router {}".format(str(r)))
            #         n = router.get("Next")
            #         LOG.info("Get Next {}".format(str(n)))
            #         fee_router = [i for i in r if i[0] not in (self.Wallet.url, receiver)]
            #         if fee_router:
            #             fee = reduce(lambda x, y:x+y,[float(i[1]) for i in fee_router])
            #         else:
            #             fee = 0
            #         LOG.info("Get Fee {}".format(str(fee)))
            #         answer = prompt("will use fee %s , Do you still want tx? [Yes/No]> " %(str(fee)))
            #         if answer.upper() in["YES","Y"]:
            #             count = float(count) + float(fee)
            #             next = r[1][0]
            #             channels = filter_channel_via_address(self.Wallet.url, next, EnumChannelState.OPENED.name)
            #             LOG.debug("Channels {}".format(str(channels)))
            #             ch = chose_channel(channels, self.Wallet.url.split("@")[0].strip(), count, asset_type)
            #             if ch:
            #                 channel_name = ch.channel
            #             else:
            #                 print("Error, can not find the channel with next router")
            #                 return None
            #             tx_nonce = trinitytx.TrinityTransaction(channel_name, self.Wallet).get_latest_nonceid()
            #             tx_nonce = int(tx_nonce)+1
            #             mg.HtlcMessage.create(channel_name, self.Wallet,self.Wallet.url, next,
            #                                  count, hr,tx_nonce, role_index=0,asset_type=asset_type,
            #                                   router=r, next_router=r[2][0], comments=comments)
            #         else:
            #             return None
            #     else:
            #         return

        elif command == "qrcode":
            enable = get_arg(arguments,1)
            if enable is None:
                self.help()
                return None
            if enable.upper() not in ["ON","OFF"]:
                print("should be on or off")
            self.qrcode = True if enable.upper() == "ON" else False

        elif command == "close":
            if not self.Channel:
                self._channel_noopen()
            channel_name = get_arg(arguments, 1)
            if channel_name is None:
                self.help()
                return None
            print("Closing channel {}".format(channel_name))
            if channel_name:
                ch.Channel.quick_close(self.Wallet, channel_name)
            else:
                print("No Channel Create")

        elif command == "peer":
            if not self.Channel:
                self._channel_noopen()
            state = get_arg(arguments,1)
            get_channel_via_address(self.Wallet.url, state)
            return
        elif command == "payment":
            asset_type = get_arg(arguments, 1)
            if not asset_type:
                print("command not give the asset type")
                return None
            value = get_arg(arguments, 2)
            if not value:
                print("command not give the count")
                return None
            comments = " ".join(arguments[3:])
            comments = comments if comments else "None"
            try:
                paycode = Payment(self.Wallet).generate_payment_code(asset_type, value, comments)
            except Exception as e:
                LOG.error(e)
                print("Get payment link error, please check the log")
                return None
            if self.qrcode:
                qrcode_terminal.draw(paycode, version=4)
            print(paycode)
            return None

        elif command == "show":
            subcommand  = get_arg(arguments,1)
            if not subcommand:
                self.help()
                return None
            if subcommand.upper() == "URI":
                print(self.Wallet.url)
            elif subcommand.upper() == "TRANS_HISTORY":
                channel_name = get_arg(arguments, 2)
                if channel_name is None:
                    print("Please provide channel")
                    return None
                tx = trinitytx.TrinityTransaction(channel_name, self.Wallet)
                result = tx.read_transaction()
                print(json.dumps(result, indent=4))
                return None
            else:
                self.help()
            return None
        elif command == "depoist_limit":
            from wallet.utils import DepositAuth
            deposit =  DepositAuth.deposit_limit()
            print("Current Deposit limit is %s TNC" %deposit)
            return None


    def _channel_noopen(self):
        print("Channel Function Can Not be Opened at Present, You can try again via channel enable")
        return False

    def handlemaessage(self):
        while self.go_on:
            if MessageList:
                message = MessageList.pop(0)
                try:
                    self._handlemessage(message[0])
                except Exception as e:
                    LOG.error("handle message error {} {}".format(json.dumps(message), str(e)))
            time.sleep(0.1)

    def _handlemessage(self,message):
        LOG.info("Handle Message: <---- {}".format(json.dumps(message)))
        if isinstance(message,str):
            message = json.loads(message)
        try:
            message_type = message.get("MessageType")
        except AttributeError:
            return "Error Message"
        if message_type  == "Founder":
            m_instance = mg.FounderMessage(message, self.Wallet)
        elif message_type in [ "FounderSign" ,"FounderFail"]:
            m_instance = mg.FounderResponsesMessage(message, self.Wallet)
        elif message_type == "Htlc":
            m_instance = mg.HtlcMessage(message, self.Wallet)
        elif message_type in ["HtlcSign", "HtlcFail"]:
            m_instance = mg.HtlcResponsesMessage(message, self.Wallet)
        elif message_type == "Rsmc":
            m_instance = mg.RsmcMessage(message, self.Wallet)
        elif message_type in ["RsmcSign", "RsmcFail"]:
            m_instance = mg.RsmcResponsesMessage(message, self.Wallet)
        elif message_type == "Settle":
            m_instance = mg.SettleMessage(message, self.Wallet)
        elif message_type in ["SettleSign","SettleFail"]:
            m_instance = mg.SettleResponseMessage(message, self.Wallet)
        elif message_type == "RResponseAck":
            m_instance = mg.RResponseAck(message,self.Wallet)
        elif message_type  == "RResponse":
            m_instance = mg.RResponse(message, self.Wallet)
        elif message_type == "RegisterChannel":
            m_instance = mg.RegisterMessage(message, self.Wallet)
        elif message_type == "CreateTranscation":
            m_instance = mg.CreateTranscation(message, self.Wallet)
        elif message_type == "TestMessage":
            m_instance = mg.TestMessage(message, self.Wallet)
        elif message_type == "PaymentLink":
            m_instance = mg.PaymentLink(message, self.Wallet)
        else:
            return "No Support Message Type "

        return m_instance.handle_message()


def main():
    parser = argparse.ArgumentParser()
    # Show the  version
    parser.add_argument("--version", action="version",
                        version=Version)
    parser.add_argument("-m", "--mainnet", action="store_true", default=False,
                        help="Use MainNet instead of the default TestNet")
    parser.add_argument("-p", "--privnet", action="store_true", default=False,
                        help="Use PrivNet instead of the default TestNet")

    args = parser.parse_args()

    if args.mainnet:
        settings.setup_mainnet()
    elif args.privnet:
        settings.setup_privnet()
    else:
        settings.setup_testnet()

    UserPrompt = UserPromptInterface()
    port = Configure.get("NetPort")
    address = Configure.get("RpcListenAddress")
    port = port if port else "20556"
    address = address if address else "0.0.0.0"
    api_server_rpc = RpcInteraceApi(port)
    endpoint_rpc = "tcp:port={0}:interface={1}".format(port, address)
    d = endpoints.serverFromString(reactor, endpoint_rpc).listen(Site(api_server_rpc.app.resource()))

    @d.addErrback
    def sys_exit(f):
        print("Setup jsonRpc server error, please check if the port {} already opened".format(port))
        os.kill(os.getpgid(os.getpid()), signal.SIGKILL)

    from wallet.Interface.tcp import GatwayClientFactory
    gateway_ip, gateway_port = Configure.get("GatewayTCP").split(":")
    f = GatwayClientFactory()
    reactor.connectTCP(gateway_ip.strip(), int(gateway_port.strip()), f)

    reactor.suggestThreadPoolSize(15)
    reactor.callInThread(UserPrompt.run)
    reactor.callInThread(UserPrompt.handlemaessage)
    reactor.callInThread(monitorblock)
    reactor.run()

if __name__ == "__main__":
    main()
