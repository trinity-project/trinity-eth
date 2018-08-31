#!/usr/bin/env python3

import os
import sys
pythonpath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(pythonpath)

import argparse
import json
import traceback
import signal
from functools import wraps, reduce
from prompt_toolkit import prompt
from twisted.internet import reactor, endpoints, protocol
from common.log import LOG, init_logger
from common.console import console_log
from lightwallet.Settings import settings
from wallet.utils import get_arg, \
    get_asset_type_name,\
    check_onchain_balance,\
    check_support_asset_type,\
    check_partner, \
    is_valid_deposit,\
    is_correct_uri, SupportAssetType,check_float_decimals
from wallet.channel import Channel, udpate_channel_when_setup
from wallet.transaction.founder import FounderMessage, FounderResponsesMessage
from wallet.transaction.payment import Payment, PaymentLink
from wallet.transaction.rsmc import RsmcMessage, RsmcResponsesMessage
from wallet.transaction.htlc import HtlcMessage, HtlcResponsesMessage, RResponse, RResponseAck
from wallet.transaction.settle import SettleMessage, SettleResponseMessage
from wallet.Interface.rpc_interface import RpcInteraceApi,CurrentLiveWallet
from wallet.event.event import EnumEventAction
from wallet.event.chain_event import event_init_wallet
from wallet.event.offchain_event import ChannelForceSettleEvent
from wallet.connection.websocket import ws_instance
from wallet.utils import get_magic
from twisted.web.server import Site
from lightwallet.prompt import PromptInterface

from wallet.Interface.rpc_interface import MessageList
import time
from model.base_enum import EnumChannelState
from wallet.Interface import gate_way
from blockchain.interface import get_block_count
from blockchain.monitor import monitorblock,EventMonitor
import requests
import qrcode_terminal
from wallet.configure import Configure


GateWayIP = Configure.get("GatewayIP")
Version = Configure.get("Version")


def wallet_opened(func):
    """

    :param func:
    :return:
    """
    @wraps(func)
    def wapper(self, *args, **kwargs):
        if not self.Wallet:
            console_log.error("No opened wallet, please open wallet first")
            return None
        else:
            return func(self, *args, **kwargs)

    return wapper


def channel_opened(func):
    """

    :param func:
    :return:
    """
    @wraps(func)
    def wapper(self, *args, **kwargs):
        if not self.Channel:
            self._channel_noopen()
            return
        else:
            return func(self,*args, **kwargs)
    return wapper


def arguments_length(length):
    """

    :param length:
    :param func:
    :return:
    """
    def wapper(func):
        def _wapper(self,arguments):
            ar_len = length if isinstance(length,list) else [length]
            if len(arguments) in ar_len:
                return func(self,arguments)
            else:
                console_log.error("Arguments length should be {}".format(ar_len))
                self.help()
                return
        return _wapper
    return wapper


class UserPromptInterface(PromptInterface):
    Channel = False

    def __init__(self):
        super().__init__()
        self.user_commands = [
            "channel enable",
            "channel create {partner} {asset_type} {deposit}",
            "channel tx {payment_link}/{receiver} {asset_type} {count}",
            "channel close {channel}",
            "channel force-close {channel} {gwei}",
            "channel peer [state=]|[peer=]|[channel=]",
            "channel payment {asset}, {count}, [{comments}]",
            "channel qrcode {on/off}",
            "channel show uri",
            "channel show trans_history {channel}",
            "channel deposit_limit",
            # "contract approve {count}",
            # "contract check-approved"
        ]
        self.commands.extend(self.user_commands)
        self.qrcode = False

    def get_address(self):
        """

        :return:
        """
        return self.Wallet.address

    def handle_commands(self,command, arguments):
        """

        :param command:
        :param arguments:
        :return:
        """
        try:
            if command is not None and len(command) > 0:
                command = command.lower()
                if command == 'channel':
                    self.do_channel(arguments)
                elif command == "faucet":
                    self.do_faucet()
                else:
                    super().handle_commands(command,arguments)
        except Exception as error:
            LOG.error(error)
            pass


    def get_bottom_toolbar(self, cli=None):
        return "[{}]{}/{}".format(settings.NET_NAME if not PromptInterface.locked else settings.NET_NAME + "(Locked)",
        str(EventMonitor.get_wallet_block_height()),str(EventMonitor.get_block_height()))


    #faucet for test tnc
    @wallet_opened
    def do_faucet(self):
        console_log.console(self.Wallet.address)
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

    @wallet_opened
    def do_close_wallet(self):
        if self.Wallet:
            self.Wallet.SaveStoredData("BlockHeight", self.Wallet.BlockHeight)
            try:
                gate_way.close_wallet()
            except Exception as e:
                LOG.error(e)
        super().do_close_wallet()

    def quit(self):
        console_log.info('Shutting down. This may take about 15 sec to sync the block info')
        self.go_on = False
        ws_instance.stop_websocket()
        EventMonitor.stop_monitor()
        self.do_close_wallet()
        CurrentLiveWallet.update_current_wallet(None)
        reactor.stop()

    def enable_channel(self):
        try:
            result = gate_way.join_gateway(self.Wallet).get("result")
            if result:
                self.Wallet.url = json.loads(result).get("MessageBody").get("Url")

                try:
                    spv = json.loads(result).get("MessageBody").get("Spv")
                    spv_port = spv.strip().split(":")[1]
                except:
                    spv_port = "8866"
                gate_way.GatewayInfo.update_spv_port(spv_port)
                self.Channel = True
                print("Channel Function Enabled")
                return True
        except requests.exceptions.ConnectionError:
            pass
        return False

    # def do_contract(self, arguments):
    #     if not self.Wallet:
    #         print("Please open a wallet")
    #         return
    #
    #     command = get_arg(arguments)
    #     asset_command = [i.split()[1] for i in self.user_commands]
    #     if command not in asset_command:
    #         print("no support command, please check the help")
    #         self.help()
    #         return
    #
    #     if command == 'approve':
    #         deposit = get_arg(arguments, 1)
    #         try:
    #             ch.Channel.approve(self.Wallet.address, deposit, self.Wallet._key.private_key_string)
    #         except Exception as error:
    #             print('Error to approved asset to contract. {}'.format(error))
    #
    #     elif command == "check-approved":
    #         try:
    #             result = ch.Channel.get_approved_asset(self.Wallet.address)
    #         except Exception as error:
    #             result = 0
    #         else:
    #             if not result:
    #                 result = 0
    #             print('Has approved {}'.format(result))
    #
    #     return
    @channel_opened
    @arguments_length([4, 5])
    def do_channel_create(self, arguments):
        """

        :return:
        """

        partner = get_arg(arguments, 1)
        if not is_correct_uri(partner):
            console_log.error("No correct uri format")
            return None

        asset_type = get_arg(arguments, 2)
        asset_type = asset_type.upper() if check_support_asset_type(asset_type) else None
        if not asset_type:
            console_log.error("No support asset, current just support {}".format(str(SupportAssetType.SupportAssetType)))
            return None

        try:
            deposit = float(get_arg(arguments, 3).strip())
            partner_deposit = get_arg(arguments, 4)
            partner_deposit = float(float(partner_deposit.strip())) if partner_deposit is not None else deposit
            if 0 >= deposit:
                console_log.error("Founder's Deposit MUST be larger than 0")
            elif 0 > partner_deposit or partner_deposit > deposit:
                console_log.error("Founder's Deposit should not be less than Partner's")
                return None
        except ValueError:
            console_log.error("Founder's Deposit should not be less than Partner'")
            return None

        if not check_onchain_balance(self.Wallet.address, asset_type, deposit):
            console_log.error("Now the balance on-chain is less than the deposit.")
            return None

        if not check_partner(self.Wallet, partner):
            console_log.error("Partner URI is not correct, Please check the partner uri")
            return None

        if not check_onchain_balance(partner.strip().split("@")[0], asset_type, partner_deposit):
            console_log.error("Partner balance on chain is less than the deposit")
            return None

        Channel.create(self.Wallet, self.Wallet.url, partner, asset_type, deposit, partner_deposit,
                       trigger=FounderMessage.create)

    @channel_opened
    @arguments_length([2,4,5])
    def channel_trans(self, arguments):
        """

        :param arguments:
        :return:
        """


        if len(arguments) ==2:
            # payment code
            pay_code = get_arg(arguments, 1)
            result, info = Payment.decode_payment_code(pay_code)
            if result:
                receiver = info.get("uri")
                net_magic = info.get('net_magic')
                if not net_magic or net_magic != str(get_magic()):
                    console_log.error("No correct net magic")
                    return None
                hashcode = info.get("hashcode")
                asset_type = info.get("asset_type")
                # asset_type = get_asset_type_name(asset_type)
                count = info.get("payment")
                comments = info.get("comments")
                console_log.info("will pay {} {} to {} comments {}".format(count, asset_type, receiver, comments))
            else:
                console_log.error("The payment code is not correct")
                return
        else:
            receiver = get_arg(arguments, 1)
            asset_type = get_arg(arguments, 2)
            count = get_arg(arguments, 3)
            hashcode = get_arg(arguments, 4)
            if not receiver or not asset_type or not count:
                self.help()
                return None

            asset_type = asset_type.upper() if check_support_asset_type(asset_type) else None
            if not asset_type:
                console_log.error("No support asset, current just support {}".format(str(SupportAssetType.SupportAssetType)))
                return None

            if 0 >= float(count):
                console_log.warn('Not support negative number or zero.')
                return None

        # query channels by address
        channel_set = Channel.get_channel(self.Wallet.url, receiver, EnumChannelState.OPENED)
        if channel_set and channel_set[0]:
            Channel.transfer(channel_set[0].channel, self.Wallet, receiver, asset_type, count, hashcode,
                             cli=True, trigger=RsmcMessage.create)
        else:
            if not hashcode:
                console_log.error("No hashcode")
                return None
            try:
                message = {"MessageType":"GetRouterInfo",
                           "Sender":self.Wallet.url,
                           "Receiver": receiver,
                           "AssetType": asset_type,
                           "NetMagic": get_magic(),
                           "MessageBody":{
                               "AssetType":asset_type,
                               "Value":count
                               }
                           }
                result = gate_way.get_router_info(message)
                routerinfo = json.loads(result.get("result"))
            except Exception as error:
                LOG.error('Exception occurred during get route info. Exception: {}'.format(error))
                console_log.warning('No router was found.')
                return
            else:
                router=routerinfo.get("RouterInfo")
                if not router:
                    LOG.error('Router between {} and {} was not found.'.format(self.Wallet.url, receiver))
                    console_log.error('Router not found for HTLC transfer.')
                    return

            full_path = router.get("FullPath")
            LOG.info("Get Router {}".format(str(full_path)))

            next_jump = router.get("Next")
            LOG.info("Get Next {}".format(str(next_jump)))
            fee_router = [i for i in full_path if i[0] not in (self.Wallet.url, receiver)]
            if fee_router:
                fee = reduce(lambda x, y:x+y,[float(i[1]) for i in fee_router])
            else:
                fee = 0

            count = HtlcMessage.float_calculate(count, fee)
            receiver = full_path[1][0]
            channel_set = Channel.get_channel(self.Wallet.url, receiver, EnumChannelState.OPENED)
            if not(channel_set and channel_set[0]):
                print('No OPENED channel was found for HTLC trade.')
                return
            LOG.info("Get Fee {}".format(str(fee)))
            answer = prompt("You will pay extra fee {}. Do you wish continue this transaction? [Yes/No]>".format(fee))
            if answer.upper() in["YES", "Y"]:
                channel_name = channel_set[0].channel
                Channel.transfer(channel_name, self.Wallet, receiver, asset_type, count, hashcode, router=full_path,
                                 next_jump=full_path[2][0], cli=True, trigger=HtlcMessage.create)

            else:
                return

    @channel_opened
    @arguments_length(2)
    def channel_qrcode(self, arguments):
        """

        :param arguments:
        :return:
        """
        enable = get_arg(arguments, 1)
        if enable.upper() not in ["ON", "OFF"]:
            console_log.error("should be on or off")
        self.qrcode = True if enable.upper() == "ON" else False
        console_log.console("Qrcode opened") if self.qrcode else console_log.info("Qrcode closed")
        return None

    @channel_opened
    @arguments_length(2)
    def channel_close(self, arguments):
        """

        :param arguments:
        :return:
        """
        channel_name = get_arg(arguments, 1)

        console_log.console("Closing channel {}".format(channel_name))
        if channel_name:
            Channel.quick_close(channel_name, wallet=self.Wallet, cli=True, trigger=SettleMessage.create)
        else:
            console_log.warn("No Channel Create")

    @channel_opened
    def channel_force_close(self, arguments):
        """

        :param arguments:
        :return:
        """
        channel_name = get_arg(arguments, 1)

        if 'debug' in arguments:
            nonce = get_arg(arguments, 2, True)
            is_debug = True
        else:
            nonce = None
            is_debug = False

        console_log.console("Force to close channel {}".format(channel_name))
        if channel_name:
            channel_event = ChannelForceSettleEvent(channel_name, True)
            channel_event.register_args(EnumEventAction.EVENT_EXECUTE,
                                        invoker_uri=self.Wallet.url, channel_name=channel_name,
                                        nonce=nonce, invoker_key=self.Wallet._key.private_key_string,
                                        is_debug=is_debug)
            ws_instance.register_event(channel_event)
        else:
            console_log.warn("No Channel Create")

    @channel_opened
    @arguments_length([1,2,3,4])
    def channel_peer(self, arguments):
        """

        :param arguments:
        :return:
        """
        arg_dic={"state":None,"peer":None,"channel":None}
        for i in range(1,4):
            arg = get_arg(arguments,i)
            if arg is None:
                continue
            try:
                k_v=arg.strip().split("=")
                if k_v[0] in arg_dic.keys():
                    arg_dic[k_v[0]]=k_v[1]
            except IndexError:
                continue
            else:
                continue

        Channel.get_channel_list(self.Wallet.url, **arg_dic)
        return

    @channel_opened
    def channel_payment(self, arguments):
        """

        :param arguments:
        :return:
        """
        asset_type = get_arg(arguments, 1)
        if not check_support_asset_type(asset_type):
            console_log.error("No support asset, current just support {}".format(SupportAssetType.SupportAssetType))
            return None
        value = get_arg(arguments, 2)
        if not value:
            console_log.error("command not give the count")
            return None
        try:
            if float(value) <=0 or not check_float_decimals(value, asset_type):
                console_log.error("value should not be less than 0")
                return None
        except ValueError:
            console_log.error("value format error")
            return None
        comments = " ".join(arguments[3:])
        comments = comments if comments else "None"
        if len(comments) > 128:
            console_log.error("comments length should be less than 128")
            return None
        try:
            hash_r, rcode = Payment.create_hr()
            Channel.add_payment(None, hash_r, rcode, value)
            paycode = Payment.generate_payment_code(self.Wallet.url, asset_type, value, hash_r, comments, True)
        except Exception as e:
            LOG.error(e)
            console_log.error("Get payment link error, please check the log")
            return None
        if self.qrcode:
            qrcode_terminal.draw(paycode, version=4)
        console_log.console(paycode)
        return None

    @channel_opened
    def channel_show(self, arguments):
        """

        :param arguments:
        :return:
        """
        subcommand = get_arg(arguments, 1)
        if not subcommand:
            self.help()
            return None
        if subcommand.upper() == "URI":
            console_log.console(self.Wallet.url)
        elif subcommand.upper() == "TRANS_HISTORY":
            channel_name = get_arg(arguments, 2)
            if channel_name is None:
                console_log.error("No provide channel")
                return None
            tx_his = Channel.batch_query_trade(channel_name)
            for tx in tx_his:
                console_log.console(tx)
            return None
        else:
            self.help()
        return None

    @channel_opened
    @arguments_length(1)
    def channel_deposit_limit(self, arguments):
        """

        :param arguments:
        :return:
        """
        from wallet.utils import DepositAuth
        deposit = DepositAuth.deposit_limit()
        console_log.info("Current Deposit limit is %s TNC" % deposit)
        return None

    @wallet_opened
    def do_channel(self,arguments):
        """

        :param arguments:
        :return:
        """
        command = get_arg(arguments)
        channel_command = [i.split()[1] for i in self.user_commands]
        if command not in channel_command:
            console_log.error("no support command, please check the help")
            self.help()
            return

        if command == 'create':
            self.do_channel_create(arguments)

        elif command == "enable":
            if not self.enable_channel():
                self._channel_noopen()

        elif command == "tx":
            self.channel_trans(arguments)

        elif command == "qrcode":
            self.channel_qrcode(arguments)

        elif command == "close":
            self.channel_close(arguments)

        elif command == "force-close":
            self.channel_force_close(arguments)

        elif command == "peer":
            self.channel_peer(arguments)

        elif command == "payment":
            self.channel_payment(arguments)

        elif command == "show":
            self.channel_show(arguments)

        elif command == "deposit_limit":
            self.channel_deposit_limit(arguments)
        else:
            return None

    def _channel_noopen(self):
        console_log.warn("Channel Function Can Not be Opened at Present, You can try again via channel enable")
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
            m_instance = FounderMessage(message, self.Wallet)

        elif message_type in [ "FounderSign" ,"FounderFail"]:
            m_instance = FounderResponsesMessage(message, self.Wallet)

        elif message_type == "Htlc":
            m_instance = HtlcMessage(message, self.Wallet)

        elif message_type in ["HtlcSign", "HtlcFail"]:
            m_instance = HtlcResponsesMessage(message, self.Wallet)

        elif message_type == "Rsmc":
            m_instance = RsmcMessage(message, self.Wallet)

        elif message_type in ["RsmcSign", "RsmcFail"]:
            m_instance = RsmcResponsesMessage(message, self.Wallet)

        elif message_type == "Settle":
            m_instance = SettleMessage(message, self.Wallet)

        elif message_type in ["SettleSign","SettleFail"]:
            m_instance = SettleResponseMessage(message, self.Wallet)

        elif message_type == "RResponseAck":
            m_instance = RResponseAck(message,self.Wallet)

        elif message_type  == "RResponse":
            m_instance = RResponse(message, self.Wallet)

        # elif message_type == "RegisterChannel":
        #     m_instance = RegisterMessage(message, self.Wallet)
        #
        # elif message_type == "CreateTranscation":
        #     m_instance = CreateTranscation(message, self.Wallet)
        #
        # elif message_type == "TestMessage":
        #     m_instance = TestMessage(message, self.Wallet)

        elif message_type == "PaymentLink":
            m_instance = PaymentLink(message)

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

    # initialize the loggers
    init_logger(file_name='wallet.log')

    UserPrompt = UserPromptInterface()
    port = Configure.get("NetPort")
    address = Configure.get("RpcListenAddress")
    port = port if port else "21556"
    address = address if address else "0.0.0.0"
    api_server_rpc = RpcInteraceApi(port)
    endpoint_rpc = "tcp:port={0}:interface={1}".format(port, address)
    d = endpoints.serverFromString(reactor, endpoint_rpc).listen(Site(api_server_rpc.app.resource()))

    @d.addErrback
    def sys_exit(f):
        console_log.warn("Setup jsonRpc server error, please check if the port {} already opened".format(port))
        os.kill(os.getpgid(os.getpid()), signal.SIGKILL)

    from wallet.Interface.tcp import GatwayClientFactory
    gateway_ip, gateway_port = Configure.get("GatewayTCP").split(":")
    f = GatwayClientFactory()
    reactor.connectTCP(gateway_ip.strip(), int(gateway_port.strip()), f)

    reactor.suggestThreadPoolSize(15)
    reactor.callInThread(UserPrompt.run)
    reactor.callInThread(UserPrompt.handlemaessage)
    reactor.callInThread(monitorblock)
    reactor.callInThread(ws_instance.handle)
    reactor.run()

if __name__ == "__main__":
    main()
