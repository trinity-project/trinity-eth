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

#coding=utf-8

from wallet.TransactionManagement.transaction import TrinityTransaction
from wallet.utils import pubkey_to_address, get_asset_type_id
from wallet.ChannelManagement import channel as ch
from model.base_enum import EnumChannelState
from wallet.Interface.gate_way import send_message
from wallet.utils import sign,\
    check_onchain_balance, \
    check_max_deposit,\
    check_mix_deposit,\
    check_deposit,\
    get_magic
from blockchain.monior import register_block, \
    register_monitor
from blockchain.ethInterface import Interface as EthInterface
from blockchain.web3client import Client as EthWebClient
from model import APIChannel
from log import LOG
import json
from wallet.TransactionManagement.payment import Payment
from enum import IntEnum
from lightwallet.Settings import settings
import time


class EnumTradeType(IntEnum):
    TRADE_TYPE_FOUNDER = 0x0
    TRADE_TYPE_RSMC = 0x10
    TRADE_TYPE_HTLC = 0x20
    TRADE_TYPE_SETTLE = 0x30


class EnumTradeRole(IntEnum):
    TRADE_ROLE_FOUNDER = 0x1
    TRADE_ROLE_PARTNER = 0x2


class EnumTradeState(IntEnum):
    confirming = 0x10
    confirmed = 0x20

    # error transaction state
    stuck_by_error_deposit = 0x80
    failed = 0xFF


class EnumResponseStatus(IntEnum):
    RESPONSE_OK = 0x0
    """
        Question: Need we define some different response ok to distinguish the transaction type ????
        .e.g:
        RESPONSE_FOUNDER_OK # for creating channel message
        RESPONSE_RSMC_OK    # for RSMC transaction message
    """

    # Founder Message
    RESPONSE_FOUNDER_DEPOSIT_LESS_THAN_PARTNER = 0x10
    RESPONSE_FOUNDER_NONCE_NOT_ZERO = 0x11

    # Common response error
    RESPONSE_EXCEPTION_HAPPENED = 0xF0
    RESPONSE_FAIL = 0XFF


class Message(object):
    """

    """

    def __init__(self, message):
        self.message = message
        self.receiver = message.get("Receiver")
        self.sender = message.get("Sender")
        #assert self.sender != self.receiver, 'Sender should be different from receiver.'

        self.message_type = message.get("MessageType")
        self.message_body = message.get("MessageBody")
        self.error = message.get("Error")
        # self.network_magic = get_magic()

        try:
            self.sender_address = self.sender.split('@')[0].strip()
            self.receiver_address = self.receiver.split('@')[0].strip()
        except Exception as error:
            LOG.error('Invalid sender<{}> or receiver<{}> format from message<{}>. Error: {}'.format(self.sender,
                                                                                                     self.receiver,
                                                                                                     self.message_type,
                                                                                                     error))
            self.sender_address = None
            self.receiver_address = None

    @property
    def network_magic(self):
        return get_magic()

    @staticmethod
    def get_magic():
        return get_magic()



    @staticmethod
    def send(message):
        send_message(message)

    def handle(self):
        LOG.info('Received Message<{}>'.format(self.message_type))


class RegisterMessage(Message):
    """
    transaction massage:
    { "MessageType":"RegisterChannel",
    "Sender": "9090909090909090909090909@127.0.0.1:20553",
    "Receiver":"101010101001001010100101@127.0.0.1:20552",
    "ChannelName":"090A8E08E0358305035709403",
    "MessageBody": {
            ""
            "AssetType": "",
            "Deposit":"",
        }
    }
    """

    def __init__(self, message, wallet):
        super().__init__(message)
        self.deposit = self.message_body.get("Deposit")
        self.asset_type = self.message_body.get("AssetType")
        self.channel_name = self.message.get("ChannelName")
        self.wallet = wallet

    def handle_message(self):
        LOG.info("Handle RegisterMessage: {}".format(json.dumps(self.message)))
        verify, error = self.verify()
        if not verify:
            message = {
                "MessageType": "RegisterChannelFail",
                "Sender": self.receiver,
                "Receiver": self.sender,
                "ChannelName": self.channel_name,
                "MessageBody": {
                    "OrigianlMessage": self.message
                },
                "Error": error
            }
            Message.send(message)
        founder_pubkey, founder_ip = self.sender.split("@")
        partner_pubkey, partner_ip = self.receiver.split("@")
        founder_address = pubkey_to_address(founder_pubkey)
        partner_address = pubkey_to_address(partner_pubkey)
        deposit = {}
        subitem = {}
        subitem.setdefault(self.asset_type, self.deposit)
        deposit[founder_pubkey] = subitem
        deposit[partner_pubkey] = subitem
        APIChannel.add_channel(self.channel_name, self.sender.strip(), self.receiver.strip(),
                               EnumChannelState.INIT.name, 0, deposit)
        FounderMessage.create(self.channel_name,partner_pubkey,founder_pubkey,
                              self.asset_type.upper(),self.deposit,founder_ip,partner_ip)

    def verify(self):
        if self.sender == self.receiver:
            return False, "Not Support Sender is Receiver"
        if self.receiver != self.wallet.url:
            return False, "The Endpoint is Not Me, I am {}".format(self.wallet.url)
        state, error = self.check_balance()
        if not state:
            return state, error
        state, error = self.check_depoist()
        if not state:
            return state, error

        return True, None

    def check_depoist(self):
        state, de = check_deposit(self.deposit)
        if not state:
            if isinstance(de,float):
                return False,"Deposit should be larger than 0 , but give {}".format(str(de))
            else:
                return False,"Deposit Formate error {}".format(de)

        state, maxd = check_max_deposit(self.deposit)
        if not state:
            if isinstance(maxd,float):
                return False, "Deposit is larger than the max, max is {}".format(str(maxd))
            else:
                return False, "Max deposit configure error {}".format(maxd)

        state , mixd = check_mix_deposit(self.deposit)
        if not state:
            if isinstance(mixd,float):
                return False, "Deposit is less than the min, min is {}".format(str(mixd))
            else:
                return False, "Mix deposit configure error {}".format(mixd)

        return True,None

    def check_balance(self):
        if check_onchain_balance(self.wallet.pubkey, self.asset_type, self.deposit):
            return True, None
        else:
            return False, "No Balance OnChain to support the deposit"


class TestMessage(Message):

    def __init__(self, message, wallet):
        super().__init__(message)
        self.wallet= wallet

    def handle_message(self):
        founder = self.wallet.url
        ch.create_channel(founder, "292929929292929292@10.10.12.1:20332", "TNC", 10)


class CreateTranscation(Message):
    """
    { "MessageType":"CreateTranscation",
    "Receiver":"101010101001001010100101@127.0.0.1:20552",
    "ChannelName":"090A8E08E0358305035709403",
    "MessageBody": {
            "AssetType":"TNC",
            "Value": 20
        }
    }
    """
    def __init__(self, message, wallet):
        super().__init__(message)
        self.wallet= wallet
        self.receiver_pubkey, self.receiver_ip = self.message.get("Receiver").split("@")
        self.channel_name = self.message.get("ChannelName")
        self.asset_type = self.message_body.get("AssetType")
        self.value = self.message_body.get("Value")
        self.gateway_ip = self.wallet.url.split("@")[1].strip()

    def handle_message(self):
        tx_nonce = TrinityTransaction(self.channel_name, self.wallet).get_latest_nonceid()
        LOG.info("CreateTransaction: {}".format(str(tx_nonce)))
        RsmcMessage.create(self.channel_name, self.wallet, self.wallet.pubkey,
                           self.receiver_pubkey, self.value, self.receiver_ip, self.gateway_ip,str(tx_nonce))

    @staticmethod
    def ack(channel_name, receiver_pubkey, receiver_ip, error_code, cli = False):
        if cli:
            print (error_code)
        else:
            return {
                "MessageType":"CreateTransactionACK",
                "Receiver":"{}@{}".format(receiver_pubkey,receiver_ip),
                "ChannelName":channel_name,
                "Error": error_code
            }


class TransactionMessage(Message):
    #__init__(self, url, contract_address, contract_abi, asset_address, asset_abi)
    _interface = None
    _web3_client = None
    _trinity_coef = pow(10, 8)
    """

    """

    def __init__(self, message, wallet):
        super().__init__(message)
        self.wallet = wallet
        self.tx_nonce = message.get("TxNonce")

    def verify(self,**kwargs):
        pass

    def sign_message(self, context):
        """
        ToDo
        :param context:
        :return:
        """
        res = sign(self.wallet, context)
        return res

    @staticmethod
    def _eth_interface():
        if not TransactionMessage._interface:
            TransactionMessage._interface = EthInterface(settings.NODEURL,
                                                         settings.Eth_Contract_address, settings.Eth_Contract_abi,
                                                         settings.TNC, settings.TNC_abi)

        return TransactionMessage._interface

    @staticmethod
    def _eth_client():
        if not TransactionMessage._web3_client:
            TransactionMessage._web3_client = EthWebClient(settings.NODEURL)

        return TransactionMessage._web3_client

    @staticmethod
    def sign_content(start=3, *args, **kwargs):
        """

        :return:
        """
        typeList = args[0] if 0 < len(args) else kwargs.get('typeList')
        valueList = args[1] if 1 < len(args) else kwargs.get('valueList')
        privtKey = args[2] if 2 < len(args) else kwargs.get('privtKey')

        for idx in range(start, len(typeList)-start):
            if typeList[idx] in ['uint256']:
                valueList[idx] = TransactionMessage.multiply(valueList[idx])

        content = TransactionMessage._eth_client().sign_args(typeList, valueList, privtKey).decode()
        return '0x' + content

    @staticmethod
    def approve(address, deposit, private_key):
        TransactionMessage._eth_interface().approve(address, TransactionMessage.multiply(deposit), private_key)

    @staticmethod
    def get_approved_asset(address):
        return TransactionMessage._eth_interface().get_approved_asset(settings.TNC,
                                                                      settings.TNC_abi,
                                                                      address,
                                                                      settings.Eth_Contract_address)

    @staticmethod
    def deposit(address, channel_id, nonce, founder, founder_amount, partner, partner_amount,
                founder_sign, partner_sign, private_key):
        TransactionMessage._eth_interface().deposit(address,channel_id, nonce,
                                                    founder, TransactionMessage.multiply(founder_amount),
                                                    partner, TransactionMessage.multiply(partner_amount),
                                                    founder_sign, partner_sign, private_key)

    @staticmethod
    def quick_settle(invoker, channel_id, nonce, founder, founder_balance,
                     partner, partner_balance, founder_signature, partner_signature, invoker_key):
        TransactionMessage._eth_interface().quick_close_channel(invoker, channel_id, nonce, founder,
                                                                founder_balance, partner, partner_balance,
                                                                founder_signature, partner_signature, invoker_key)

    @staticmethod
    def multiply(asset_count):
        return int(asset_count * TransactionMessage._trinity_coef)

    @staticmethod
    def divide(asset_count):
        return asset_count / TransactionMessage._trinity_coef

    @staticmethod
    def sync_timer(callback, expected_result, timeout = 60, *args, **kwargs):
        # TODO: One temporary solution to handle some actions which approve message to on-chain
        # TODO: please delete this function if monitor event is ready
        total_timeout = timeout

        while 0 < total_timeout:
            result = callback(*args, **kwargs)
            print(result)
            
            if result:
                print(result)
                break
            
            total_timeout  = total_timeout - 15
            time.sleep(15)



class FounderMessage(TransactionMessage):
    """
    {
        "MessageType": "Founder",
        "Sender": founder,
        "Receiver": partner,
        "TxNonce": 0,
        "ChannelName": channel_name,
        "NetMagic": magic,
        "MessageBody": {
            "FounderDeposit": founder_deposit,
            "PartnerDeposit": partner_deposit,
            "Commitment": commitment,
            "AssetType": asset_type.upper(),
        }
    }
    transaction massage:
    { "MessageType":"Founder",
    "Sender": "9090909090909090909090909@127.0.0.1:20553",
    "Receiver":"101010101001001010100101@127.0.0.1:20552",
    "TxNonce": 0,
    "ChannelName":"090A8E08E0358305035709403",
    "MessageBody": {
            "Founder": "",
            "Commitment":"",
            "RevocableDelivery":"",
            "AssetType":"TNC",
            "Deposit": 10,
            "RoleIndex":0
                    }
    }
    """


    def __init__(self, message, wallet=None):
        super().__init__(message,wallet)
        # assert 0 == self.tx_nonce, 'Nonce must be zero.'

        self.channel_name = message.get("ChannelName")
        self.asset_type = self.message_body.get("AssetType")
        self.founder_deposit = self.message_body.get("FounderDeposit")
        self.partner_deposit = self.message_body.get("PartnerDeposit")

        self.commitment = self.message_body.get('Commitment')
        self.comments = self.message.get("Comments")

        self.wallet = wallet

    def handle_message(self):
        self.handle()

    def handle(self):
        super().handle()
        verify, error = self.verify()

        status = EnumResponseStatus.RESPONSE_OK
        if not verify:
            status = EnumResponseStatus.RESPONSE_FAIL
        else:
            founder_addr = self.sender.strip().split('@')[0]
            partner_addr = self.receiver.strip().split('@')[0]
            try:
                FounderMessage.approve(self.receiver.strip().split('@')[0], self.partner_deposit,
                                       self.wallet._key.private_key_string)
            except Exception as error:
                LOG.error(type(error), error)

            # TODO: currently, here wait for result with 60 seconds.
            # TODO: need trigger later by async mode
            FounderMessage.sync_timer(FounderMessage.get_approved_asset, '', 60, self.receiver.strip().split('@')[0])

            # add channel to dbs
            channel_inst = ch.Channel(self.sender, self.receiver)
            channel_inst.add_channel(channel = self.channel_name, src_addr = self.sender,
                                     dest_addr = self.receiver,
                                     state = EnumChannelState.INIT.name,
                                     deposit = {founder_addr:{self.asset_type.upper(): self.founder_deposit},
                                                partner_addr:{self.asset_type.upper(): self.partner_deposit}})
            # update channel state
            channel_inst.channel(self.channel_name).update_channel(state=EnumChannelState.OPENING.name)
            LOG.info('Channel<{}> in opening state.'.format(self.channel_name))

        # send response
        FounderResponsesMessage.create(self.channel_name, self.sender, self.receiver, self.asset_type,
                                       self.founder_deposit, self.partner_deposit, self.commitment,
                                       self.network_magic, status, self.wallet)

    @staticmethod
    def create(channel_name, founder, partner, asset_type, founder_deposit, partner_deposit, magic, wallet=None, comments=None):
        """

        :param channel_name:
        :param founder:
        :param partner:
        :param asset_type:
        :param founder_deposit:
        :param receiver_deposit:
        :param wallet:
        :param comments:
        :return:
        """
        assert founder.__contains__('@'), 'Invalid founder URL format.'
        assert partner.__contains__('@'), 'Invalid founder URL format.'

        founder_deposit = float(founder_deposit)
        assert 0 < float(founder_deposit), 'Deposit Must be lager than zero.'

        if partner_deposit:
            assert float(partner_deposit) <= float(founder_deposit), 'Deposit Must be lager than zero.'
            partner_deposit = float(partner_deposit)
        else:
            partner_deposit = founder_deposit

        founder_addr = founder.strip().split('@')[0]
        partner_addr = partner.strip().split('@')[0]

        # Sign this data to the
        commitment = FounderMessage.sign_content(typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
                                                 valueList=[channel_name, 0, founder_addr, founder_deposit, partner_addr, partner_deposit],
                                                 privtKey = wallet._key.private_key_string)

        message = {
            "MessageType": "Founder",
            "Sender": founder,
            "Receiver": partner,
            "TxNonce": 0,
            "ChannelName": channel_name,
            "NetMagic": magic,
            "MessageBody": {
                "FounderDeposit": founder_deposit,
                "PartnerDeposit": partner_deposit,
                "Commitment": commitment,
                "AssetType": asset_type.upper(),
            }
        }

        # Add comments in the messages
        if comments:
            message.update({"Comments": comments})

        # authourized the deposit to the contract
        try:
            FounderMessage.approve(founder_addr, founder_deposit, wallet._key.private_key_string)
        except Exception as e:
            print(e)

        # TODO: currently, here wait for result with 60 seconds.
        # TODO: need trigger later by async mode
        FounderMessage.sync_timer(FounderMessage.get_approved_asset, '', 60, founder_addr)

        # add channel
        # channel: str, src_addr: str, dest_addr: str, state: str, alive_block: int,
        # deposit:dict
        ch.Channel(founder, partner).add_channel(channel = channel_name, src_addr = founder, dest_addr = partner,
                                                 state = EnumChannelState.INIT.name,
                                                 deposit = {founder_addr:{asset_type.upper(): founder_deposit},
                                                            partner_addr: {asset_type.upper(): partner_deposit}})
        # record this transaction
        ch.Channel.add_trade(channel_name,
                             nonce = 0,
                             type = EnumTradeType.TRADE_TYPE_FOUNDER.value,
                             role = EnumTradeRole.TRADE_ROLE_FOUNDER,
                             address = founder,
                             balance = {asset_type.upper(): founder_deposit},
                             commitment = commitment,
                             peer = partner,
                             peer_balance = {asset_type.upper(): partner_deposit},
                             peer_commitment = None,
                             state = EnumTradeState.confirming.name)

        FounderMessage.send(message)

    def verify(self):
        return True, None



class FounderResponsesMessage(TransactionMessage):
    """
    { "MessageType":"FounderSign",
      "Sender": self.receiver,
      "Receiver":self.sender,
      "TxNonce": 0,
      "ChannelName":"090A8E08E0358305035709403",
      "MessageBody": {"founder": self.founder,
                   "Commitment":self.commitment,
                   "RevocableDelivery":self.revocabledelivery,
                   "AssetType": self.asset_type.upper(),
                    "Deposit": self.deposit,
                    "RoleIndex": role_index,
                    "Comments"："retry"

                    }
    }
    """
    def __init__(self, message, wallet):
        super().__init__(message,wallet)
        # assert 0 == self.tx_nonce, 'Nonce must be zero.'

        self.channel_name    = self.message.get("ChannelName")
        self.asset_type      = self.message_body.get("AssetType")
        self.founder_deposit = self.message_body.get("FounderDeposit")
        self.partner_deposit = self.message_body.get("PartnerDeposit")

        self.commitment = self.message_body.get('Commitment')
        self.status     = self.message.get('Status')
        self.comments   = self.message.get("Comments")

    def send_founder_raw_transaction(self):
        signdata = self.founder.get("txDataSign")
        txdata = self.founder.get("originalData").get("txData")
        signdata_self = self.sign_message(txdata)

        witnes = self.founder.get("originalData").get("witness").format(signOther=signdata,
                                                                        signSelf=signdata_self)
        return TrinityTransaction.sendrawtransaction(TrinityTransaction.genarate_raw_data(txdata, witnes))

    def update_transaction(self):
        sender_pubkey, sender_ip = self.sender.split("@")
        receiver_pubkey, receiver_ip = self.receiver.split("@")
        subitem = {}
        subitem.setdefault(self.asset_type.upper(), self.deposit)
        balance = {}
        balance.setdefault(sender_pubkey, subitem)
        balance.setdefault(receiver_pubkey, subitem)
        self.transaction.update_transaction(str(self.tx_nonce), Balance=balance, State="confirm")

    def handle_message(self):
        self.handle()

    def handle(self):
        super(FounderResponsesMessage, self).handle()

        if not (EnumResponseStatus.RESPONSE_OK.name == self.status):
            LOG.error('Founder failed to create channels. Status<{}>'.format(self.status))
            return

        verified, error = self.verify()
        if verified:
            # update transaction
            ch.Channel.update_trade(self.channel_name, self.tx_nonce, peer_commit = self.commitment)

            founder = ch.Channel.query_trade(self.channel_name, nonce=0)[0]
            if founder:
                FounderResponsesMessage.deposit(founder.address, self.channel_name, 0,
                                                founder.address, founder.balance.get(self.asset_type.upper()),
                                                founder.peer, founder.peer_commitment.get(self.asset_type.upper()),
                                                founder.commitment, founder.peer_commitment,
                                                self.wallet._key.private_key_string)

                # ToDo: need monitor event to trigger confirmed transaction
                # change channel state to OPENING
                ch.Channel(self.receiver, self.sender).channel(self.channel_name).update_channel(state = EnumChannelState.OPENING.name)
                LOG.info('Channel<{}> in opening state.'.format(self.channel_name))
            else:
                LOG.error('Error to broadcast Founder to block chain.')

        else:
            LOG.error('Handle FounderSign failed: {}'.format(error))

    def verify(self):
        if self.sender == self.receiver:
            return False, "Not Support Sender is Receiver"
        if self.receiver != self.wallet.url:
            return False, "The Endpoint is Not Me"
        return True, None

    @staticmethod
    def create(channel_name, founder, partner, asset_type, founder_deposit, founder_commitment, partner_deposit,
               magic, response_status, wallet=None, comments=None):
        """

        :param channel_name:
        :param founder:
        :param partner:
        :param asset_type:
        :param founder_deposit:
        :param receiver_deposit:
        :param wallet:
        :param comments:
        :return:
        """
        assert founder.__contains__('@'), 'Invalid founder URL format.'
        assert partner.__contains__('@'), 'Invalid founder URL format.'

        asset_type = asset_type.upper()
        commitment = None
        message = {
            "MessageType": "FounderSign",
            "Sender": partner,
            "Receiver": founder,
            "TxNonce": 0,
            "ChannelName": channel_name,
            "NetMagic": magic
        }
        trade_state = EnumTradeState.confirming

        if response_status == EnumResponseStatus.RESPONSE_OK:
            try:
                founder_deposit = float(founder_deposit)
                partner_deposit = float(partner_deposit)

                if not (0 < partner_deposit <= founder_deposit):
                    response_status = EnumResponseStatus.RESPONSE_FOUNDER_DEPOSIT_LESS_THAN_PARTNER
                    LOG.error('Invalid deposit. founder<{}> MUST be not less than partner<{}>.'.format(founder_deposit,
                                                                                                       partner_deposit))
                    trade_state = EnumTradeState.stuck_by_error_deposit
                    raise Exception(response_status.name)

                founder_addr = founder.strip().split('@')[0]
                partner_addr = partner.strip().split('@')[0]

                # Sign this data to the
                commitment = FounderMessage.sign_content(typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
                                                         valueList=[channel_name, 0, founder_addr, founder_deposit, partner_addr, partner_deposit],
                                                         privtKey = wallet._key.private_key_string)

                message.update({
                    "MessageBody": {
                        "Commitment": commitment,
                        "AssetType": asset_type
                    }
                })
            except Exception as error:
                if response_status == EnumResponseStatus.RESPONSE_OK:
                    response_status = EnumResponseStatus.RESPONSE_EXCEPTION_HAPPENED

                if EnumTradeState.confirmed == trade_state:
                    trade_state = EnumTradeState.failed

                LOG.error('Exception occurred. {}'.format(error))

        # fill message status
        message.update({'Status': response_status.name})

        # record transaction
        ch.Channel.add_trade(channel_name,
                             nonce = 0,
                             type = EnumTradeType.TRADE_TYPE_FOUNDER.value,
                             role = EnumTradeRole.TRADE_ROLE_PARTNER,
                             address = partner,
                             balance = {asset_type: partner_deposit},
                             commitment = commitment,
                             peer = founder,
                             peer_balance = {asset_type: founder_deposit},
                             peer_commitment = founder_commitment,
                             state = trade_state.name)

        # Add comments in the messages
        if comments:
            message.update({"Comments": comments})

        FounderResponsesMessage.send(message)


class RsmcMessage(TransactionMessage):
    """
    { "MessageType":"Rsmc",
    "Sender": "9090909090909090909090909@127.0.0.1:20553",
    "Receiver":"101010101001001010100101@127.0.0.1:20552",
    "TxNonce": 1,
    "ChannelName":"902ae9090232048575",
    "MessageBody": {
            "Commitment":"",
            "RevocableDelivery":"",
            "BreachRemedy":"",
            "Value":"",
            "AssetType":"TNC",
            "RoleIndex":0,
            "Comments":None
        }
    }
    """

    def __init__(self, message, wallet):
        super().__init__(message,wallet)

        self.channel_name = message.get("ChannelName")

        self.asset_type = self.message_body.get("AssetType")
        self.payment_count = self.message_body.get("PaymentCount")
        self.sender_balance = self.message_body.get("SenderBalance")
        self.receiver_balance = self.message_body.get("ReceiverBalance")
        self.commitment         = self.message_body.get('Commitment')
        self.comments = self.message.get("Comments")

    def handle_message(self):
        self.handle()

    def handle(self):
        super(RsmcMessage, self).handle()
        verified, error = self.verify()
        if verified:
            RsmcResponsesMessage.create(self.channel_name, self.wallet, self.sender, self.receiver,
                                        self.sender_balance, self.receiver_balance, self.payment_count,
                                        self.tx_nonce, self.commitment)

            pass
        else:
            LOG.error('Handle RsmcMessage error: {}'.format(error))
        pass

    @staticmethod
    def create(channel_name, wallet, sender, receiver, payment, asset_type="TNC",
               cli=False, router = None, next_router=None, comments=None):
        """

        :param channel_name:
        :param wallet:
        :param sender:
        :param receiver:
        :param payment:
        :param nounce:
        :param asset_type:
        :param cli:
        :param router:
        :param next_router:
        :param role_index:
        :param comments:
        :return:
        """
        try:
            message = RsmcMessage.generateRSMC(channel_name, wallet, sender, receiver, payment,
                                               asset_type, cli, router, next_router, comments)
            RsmcMessage.send(message)

        except Exception as error:
            LOG.error(error)
            return

    @staticmethod
    def generateRSMC(channel_name, wallet, sender, receiver, payment, asset_type="TNC",
                     cli=False, router=None, next_router=None, comments=None):
        """

        :param channel_name:
        :param wallet:
        :param sender:
        :param receiver:
        :param payment:
        :param nounce:
        :param asset_type:
        :param cli:
        :param router:
        :param next_router:
        :param role_index:
        :param comments:
        :return:
        """
        assert sender.__contains__('@'), 'Invalid sender<{}> URL format'.format(sender)
        assert receiver.__contains__('@'), 'Invalid receiver<{}> URL format.'.format(receiver)

        channel = ch.Channel.channel(channel_name)

        # get trade history
        transaction = channel.latest_trade(channel_name)
        # get nonce in the offline account book
        if not transaction:
            return
        nonce = transaction.nonce + 1

        balance = channel.get_balance()
        assert balance, 'Void balance<{}> for asset <{}>.'.format(balance, asset_type)

        sender_addr = sender.strip().split('@')[0]
        receiver_addr = receiver.strip().split('@')[0]
        asset_type = asset_type.upper()
        payment = float(payment)

        sender_balance = float(balance.get(sender_addr, {}).get(asset_type, 0))
        assert 0 < payment <= sender_balance, 'Sender balance<{}> is not enough.'.format(sender_balance)
        receiver_balance = float(balance.get(receiver_addr, {}).get(asset_type, 0))
        
        # calculate the balances of both
        sender_balance      = sender_balance - payment
        receiver_balance    = receiver_balance + payment

        # sender sign
        commitment = RsmcMessage.sign_content(
            typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
            valueList=[channel_name, nonce, sender_addr, sender_balance, receiver_addr, receiver_balance],
            privtKey = wallet._key.private_key_string)

        # TODO: MUST record this commitment and balance info
        # add the transaction history
        ch.Channel.add_trade(channel_name,
                             nonce = nonce,
                             type = EnumTradeType.TRADE_TYPE_RSMC.value,
                             role = EnumTradeRole.TRADE_ROLE_FOUNDER,
                             payment = payment,
                             address = sender,
                             balance = {asset_type.upper(): sender_balance},
                             commitment = commitment,
                             peer = receiver,
                             peer_balance = {asset_type.upper(): receiver_balance},
                             peer_commitment = None,
                             state = EnumTradeState.confirming)

        message = {
            "MessageType":"Rsmc",
            "Sender": sender,
            "Receiver": receiver,
            "TxNonce": nonce,
            "ChannelName":channel_name,
            "NetMagic": RsmcMessage.get_magic(),
            "MessageBody": {
                "AssetType":asset_type.upper(),
                "PaymentCount": payment,
                "SenderBalance": sender_balance,
                "ReceiverBalance": receiver_balance,
                "Commitment": commitment,
            }
        }

        if comments:
            message.update({"Comments": comments})

        return message


    # def _check_balance(self, balance):
    #     pass

    def verify(self):
        # assert 0 == self.tx_nonce, 'Nonce MUST be larger than zero'
        if 0 >= self.tx_nonce:
            return False, 'Nonce MUST be larger than zero'
        return True, None

    # def store_monitor_commitement(self):
    #     ctxid = self.commitment.get("txID")
    #     self.transaction.update_transaction(str(self.tx_nonce), MonitorTxId=ctxid)
    #
    # def _handle_0_message(self):
    #     LOG.info("RSMC handle 0 message {}".format(json.dumps(self.message)))
    #     # recorc monitor commitment txid
    #     self.store_monitor_commitement()
    #     self.send_responses()
    #
    #     # send 1 message
    #     RsmcMessage.create(self.channel_name,self.wallet,
    #                            self.receiver_pubkey,self.sender_pubkey,
    #                            self.value,self.sender_ip,self.receiver_ip,self.tx_nonce,
    #                        asset_type=self.asset_type.upper(), role_index= 1, comments=self.comments)
    #
    #
    # def _handle_1_message(self):
    #     LOG.info("RSMC handle 1 message  {}".format(json.dumps(self.message)))
    #     self.store_monitor_commitement()
    #     self.send_responses()
    #
    #     # send 2 message
    #     RsmcMessage.create(self.channel_name, self.wallet,
    #                        self.receiver_pubkey, self.sender_pubkey,
    #                        self.value, self.sender_ip, self.receiver_ip, self.tx_nonce,
    #                        asset_type=self.asset_type.upper(), role_index=2, comments=self.comments)
    #
    # def _handle_2_message(self):
    #     # send 3 message
    #     self.transaction.update_transaction(str(self.tx_nonce), BR=self.breach_remedy)
    #     RsmcMessage.create(self.channel_name, self.wallet,
    #                        self.receiver_pubkey, self.sender_pubkey,
    #                        self.value, self.sender_ip, self.receiver_ip, self.tx_nonce,
    #                        asset_type=self.asset_type.upper(), role_index=3, comments=self.comments)
    #     self.confirm_transaction()
    #
    # def _handle_3_message(self):
    #     self.transaction.update_transaction(str(self.tx_nonce), BR=self.breach_remedy)
    #     self.confirm_transaction()
    #
    # def confirm_transaction(self):
    #     ctx = self.transaction.get_tx_nonce(str(self.tx_nonce))
    #     monitor_ctxid = ctx.get("MonitorTxId")
    #     txData = ctx.get("RD").get("originalData").get("txData")
    #     txDataself = self.sign_message(txData)
    #     txDataother = self.sign_message(ctx.get("RD").get("txDataSign")),
    #     witness = ctx.get("RD").get("originalData").get("witness")
    #     register_monitor(monitor_ctxid, monitor_height, txData + witness, txDataother, txDataself)
    #     balance = self.transaction.get_balance(str(self.tx_nonce))
    #     self.transaction.update_transaction(str(self.tx_nonce), State="confirm")
    #     ch.Channel.channel(self.channel_name).update_channel(balance=balance)
    #     ch.sync_channel_info_to_gateway(self.channel_name, "UpdateChannel")
    #     last_tx = self.transaction.get_tx_nonce(str(int(self.tx_nonce) - 1))
    #     monitor_ctxid = last_tx.get("MonitorTxId")
    #     btxDataself = ctx.get("BR").get("originalData").get("txData")
    #     btxsignself = self.sign_message(btxDataself)
    #     btxsignother =  ctx.get("BR").get("txDataSign")
    #     bwitness = ctx.get("BR").get("originalData").get("witness")
    #     try:
    #         self.confirm_payment()
    #     except Exception as e:
    #         LOG.info("Confirm payment error {}".format(str(e)))
    #
    #     register_monitor(monitor_ctxid, monitor_height, btxDataself + bwitness, btxsignother, btxsignself)

    def confirm_payment(self):
        for key, value in Payment.HashR.items():
            if key == self.comments:
                PaymentAck.create(value[1], key)
                Payment(self.wallet,value[1]).delete_hr(key)

    # def send_responses(self, error = None):
    #     if not error:
    #         commitment_sig = {"txDataSign": self.sign_message(self.commitment.get("txData")),
    #                           "originalData": self.commitment}
    #         rd_sig = {"txDataSign": self.sign_message(self.revocable_delivery.get("txData")),
    #                   "originalData": self.revocable_delivery}
    #         message_response = {"MessageType": "RsmcSign",
    #                             "Sender": self.receiver,
    #                             "Receiver": self.sender,
    #                             "TxNonce": self.tx_nonce,
    #                             "ChannelName": self.channel_name,
    #                             "MessageBody": {"Commitment": commitment_sig,
    #                                             "RevocableDelivery": rd_sig,
    #                                             "Value": self.value,
    #                                             "RoleIndex": self.role_index,
    #                                             "Comments":self.comments
    #                                             }
    #                             }
    #         self.send(message_response)
    #     else:
    #         message_response = {"MessageType": "RsmcFail",
    #                             "Sender": self.receiver,
    #                             "Receiver": self.sender,
    #                             "TxNonce": self.tx_nonce,
    #                             "ChannelName": self.channel_name,
    #                             "MessageBody": {"Commitment": self.commitment,
    #                                             "RevocableDelivery": self.revocable_delivery,
    #                                             "Value": self.value,
    #                                             "RoleIndex": self.role_index,
    #                                             "Comments":self.comments
    #                                             },
    #                             "Error": error
    #                             }
    #         self.send(message_response)
    #         LOG.info("Send RsmcMessage Response {}".format(json.dumps(message_response)))


class RsmcResponsesMessage(TransactionMessage):
    """
    { "MessageType":"RsmcSign",
      "Sender": self.receiver,
      "Receiver":self.sender,
      "TxNonce": 0,
      "ChannelName":"090A8E08E0358305035709403",
      "MessageBody": {
                   "Commitment":{}
                   "RevocableDelivery":"
                   "BreachRemedy":""
                    }
    }
    """
    def __init__(self, message, wallet):
        super().__init__(message,wallet)
        self.channel_name = message.get("ChannelName")
        self.channel = None

        self.asset_type     = self.message_body.get("AssetType", '').upper()
        self.payment_count  = self.message_body.get("PaymentCount")
        self.sender_balance = self.message_body.get("SenderBalance")
        self.receiver_balance = self.message_body.get("ReceiverBalance")
        self.commitment = self.message_body.get('Commitment')
        self.comments   = self.message.get("Comments")
        self.status     = self.message.get('Status')

    def handle_message(self):
        self.handle()

    def handle(self):
        super(RsmcResponsesMessage, self).handle()

        verified, error = self.verify()
        if verified:
            if EnumResponseStatus.RESPONSE_OK.name == self.status:
                # update channel balance
                sender_addr = self.sender.strip().split('@')[0]
                receiver_addr = self.receiver.strip().split('@')[0]
                self.channel = ch.Channel(self.sender, self.receiver).channel(self.channel_name)
                self.channel.update_channel(balance={sender_addr: {self.asset_type: self.sender_balance},
                                                     receiver_addr: {self.asset_type: self.receiver_balance}})

            # TODO: update transaction information
            LOG.info('update transaction')
        else:
            LOG.error('Handle RsmcRespnose error: {}'.format(error))

    @staticmethod
    def create(channel_name, wallet, sender, receiver, sender_balance, receiver_balance, payment, tx_nonce,
               sender_commitment, asset_type="TNC", cli=False, router = None, next_router=None, comments=None):
        """

        :param channel_name:
        :param wallet:
        :param sender:
        :param receiver:
        :param sender_balance:
        :param receiver_balance:
        :param payment:
        :param nonce:
        :param asset_type:
        :param cli:
        :param router:
        :param next_router:
        :param comments:
        :return:
        """
        channel = ch.Channel.channel(channel_name)

        # get trade history
        transaction = channel.latest_trade(channel_name)
        # get nonce in the offline account book
        if not transaction:
            return
        nonce = transaction.nonce + 1
        trade_state = EnumTradeState.confirmed
        balance = channel.get_balance()

        commitment = None
        status = EnumResponseStatus.RESPONSE_OK

        try:
            assert sender.__contains__('@'), 'Invalid sender<{}> URL format'.format(sender)
            assert receiver.__contains__('@'), 'Invalid receiver<{}> URL format.'.format(receiver)
            assert balance, 'Void balance<{}> for asset <{}>.'.format(balance, asset_type)

            sender_addr     = sender.strip().split('@')[0]
            receiver_addr   = receiver.strip().split('@')[0]
            asset_type      = asset_type.upper()
            payment         = float(payment)

            this_sender_balance = float(balance.get(sender_addr, {}).get(asset_type, 0))
            this_receiver_balance = float(balance.get(receiver_addr, {}).get(asset_type, 0))

            # calculate the balances of both
            this_sender_balance      = this_sender_balance - payment
            this_receiver_balance    = this_receiver_balance + payment

            assert (0 < this_sender_balance == float(sender_balance)), \
                'Unmatched balance of sender<{}>, balance<{}:{}>, payment<{}>'.format(sender, sender_balance,
                                                                                      this_sender_balance, payment)
            assert (0 < this_receiver_balance == float(receiver_balance)), \
                'Unmatched balance of sender<{}>, balance<{}:{}>, payment<{}>'.format(receiver, receiver_balance,
                                                                                      this_receiver_balance, payment)


            # sender sign
            commitment = RsmcMessage.sign_content(
                typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
                valueList=[channel_name, nonce, sender_addr, sender_balance, receiver_addr, receiver_balance],
                privtKey = wallet._key.private_key_string)

            # update channel balance
            channel.update_channel(balance={sender_addr: {asset_type: this_sender_balance},
                                            receiver_addr: {asset_type: this_receiver_balance}})
        except Exception as error:
            trade_state = EnumTradeState.failed
            LOG.exception(error)
            status = EnumResponseStatus.RESPONSE_EXCEPTION_HAPPENED

        # TODO: MUST record this commitment and balance info
        # add the transaction history
        ch.Channel.add_trade(channel_name,
                             nonce = nonce,
                             type = EnumTradeType.TRADE_TYPE_RSMC.value,
                             role = EnumTradeRole.TRADE_ROLE_PARTNER,
                             payment = payment,
                             address = receiver,
                             balance = {asset_type.upper(): this_receiver_balance},
                             commitment = commitment,
                             peer = sender,
                             peer_balance = {asset_type.upper(): this_sender_balance},
                             peer_commitment = sender_commitment,
                             state = trade_state.name)

        message = {
            "MessageType":"RsmcSign",
            "Sender": receiver,
            "Receiver": sender,
            "TxNonce": nonce,
            "ChannelName":channel_name,
            "NetMagic": RsmcMessage.get_magic(),
            "MessageBody": {
                "AssetType":asset_type.upper(),
                "PaymentCount": payment,
                "SenderBalance": this_receiver_balance,
                "ReceiverBalance": this_sender_balance,
                "Commitment": commitment,
            }
        }

        message.update({'Status': status.name})

        if comments:
            message.update({"Comments": comments})

        RsmcResponsesMessage.send(message)

        return status

    def verify(self):
        return True, None


class RResponse(TransactionMessage):
    """
    { "MessageType":"RResponse",
    "Sender": "9090909090909090909090909@127.0.0.1:20553",
    "Receiver":"101010101001001010100101@127.0.0.1:20552",
    "TxNonce": 0,
    "ChannelName":"3333333333333333333333333333",
    "MessageBody": {
            "HR":hr,
            "R":r,
            "Comments":comments
            }
    }
    """

    def __init__(self,message, wallet):
        super().__init__(message,wallet)
        self.channel_name = message.get("ChannelName")
        self.tx_nonce = message.get("TxNonce")
        self.hr = self.message_body.get("HR")
        self.r = self.message_body.get("R")
        self.count = self.message_body.get("Count")
        self.asset_type = self.message_body.get("AssetType")
        self.comments = self.message_body.get("Comments")
        self.transaction = TrinityTransaction(self.channel_name, self.wallet)

    @staticmethod
    def create(sender, receiver, tx_nonce, channel_name, hr, r, value, asset_type, comments):
        message = { "MessageType":"RResponse",
                    "Sender": sender,
                    "Receiver":receiver,
                    "TxNonce": tx_nonce,
                    "ChannelName":channel_name,
                    "MessageBody": {
                           "HR":hr,
                           "R":r,
                           "Count":value,
                           "AssetType":asset_type,
                           "Comments":comments
                         }
                   }
        Message.send(message)

    def verify(self):
        if self.receiver != self.wallet.url:
            return False, "Not Send to me"
        if Payment.verify_hr(self.hr, self.r):
            return True, None
        else:
            return False, "Not find r"

    def handle_message(self):
        verify, error = self.verify()
        if verify:
            self.transaction.update_transaction(str(self.tx_nonce), State="confirm")
            sender_pubkey, gateway_ip = self.wallet.url.split("@")
            receiver_pubkey, partner_ip = self.sender.split("@")
            tx_nonce = int(self.tx_nonce)+1

            RsmcMessage.create(self.channel_name, self.wallet, sender_pubkey, receiver_pubkey, self.count,
                               partner_ip, gateway_ip, asset_type=self.asset_type,
               role_index=0, comments=self.hr)
            payment = Payment.get_hash_history(self.hr)

            if payment:
                channel_name = payment.get("Channel")
                LOG.debug("Payment get channel {}/{}".format(json.dumps(payment), channel_name))
                count = payment.get("Count")
                peer = ch.Channel.channel(channel_name).get_peer(self.wallet.url)
                LOG.info("peer {}".format(peer))
                RResponse.create(self.wallet.url,peer,self.tx_nonce, channel_name,
                                 self.hr, self.r, count, self.asset_type, self.comments)
                transaction = TrinityTransaction(channel_name, self.wallet)
                transaction.update_transaction(str(self.tx_nonce),State="confirm")
                Payment.update_hash_history(self.hr, channel_name, count, "confirm")
            else:
                return None
        else:
            message = { "MessageType":"RResponseAck",
                        "Sender": self.receiver,
                        "Receiver":self.sender,
                        "TxNonce": self.tx_nonce,
                        "ChannelName":self.channel_name,
                        "MessageBody": self.message_body,
                        "Error":error
                     }
            Message.send(message)
        return None


class RResponseAck(TransactionMessage):
    """
     { "MessageType":"RResponseAck",
                        "Sender": self.receiver,
                        "Receiver":self.sender,
                        "TxNonce": self.tx_nonce,
                        "ChannelName":self.channel_name,
                        "MessageBody": self.message_body,
                        "Error":error
                     }
    """

    def __init__(self, message, wallet):
        super().__init__(message,wallet)

    def handle_message(self):
        print(json.dumps(self.message, indent=4))


class HtlcMessage(TransactionMessage):
    """
    { "MessageType":"Htlc",
    "Sender": "9090909090909090909090909@127.0.0.1:20553",
    "Receiver":"101010101001001010100101@127.0.0.1:20552",
    "TxNonce": 0,
    "ChannelName":"3333333333333333333333333333",
    "Router":[],
    "Next":"",
    "MessageBody": {
            "HCTX":"",
            "RDTX":"",
            "HEDTX":"",
            "HTTX":"",
            "HTDTX":"",
            "HTRDTX":"",
            "RoleIndex":"",
            "Comments":""
        }
    }
    """

    def __init__(self, message, wallet):
        super().__init__(message,wallet)
        self.hctx = self.message_body.get("HCTX")
        self.hedtx = self.message_body.get("HEDTX")
        self.rdtx = self.message_body.get("RDTX")
        self.httx = self.message_body.get("HTTX")
        self.htdtx = self.message_body.get("HTDTX")
        self.htrdtx = self.message_body.get("HTRDTX")
        self.role_index = self.message_body.get("RoleIndex")
        self.channel_name = message.get("ChannelName")
        self.value = self.message_body.get("Value")
        self.comments = self.message_body.get("Comments")
        self.router = self.message.get("Router")
        self.next = self.message.get("Next")
        self.count = self.message_body.get("Count")
        self.asset_type = self.message_body.get("AssetType")
        self.hr = self.message_body.get("HashR")
        self.transaction = TrinityTransaction(self.channel_name, self.wallet)

    def handle_message(self):
        verify, error = self.verify()
        if verify:
            if self.role_index ==0:
                self._handle_0_message()
            elif self.role_index ==1:
                self._handle_1_message()
        else:
            self.send_responses(self.role_index,error = error)

    def verify(self):
        return True, None

    def check_if_the_last_router(self):
        return self.wallet.url == self.router[-1][0]


    def _handle_0_message(self):
        Payment.update_hash_history(self.hr, self.channel_name, self.count, "pending")
        self.send_responses(self.role_index)
        self.transaction.update_transaction(str(self.tx_nonce), TxType = "HTLC", HEDTX=self.hedtx,
                                            HR=self.hr,Count=self.count,State ="pending")
        HtlcMessage.create(self.channel_name, self.wallet, self.wallet.url, self.sender, self.count, self.hr,
                           self.tx_nonce, 1, self.asset_type, self.router,
                           self.next, comments=self.comments)

        if self.check_if_the_last_router():
            pass
        else:
            next = self.get_next_router()
            LOG.debug("Get Next Router {}".format(str(next)))
            channels = ch.filter_channel_via_address(self.wallet.url, next, state=EnumChannelState.OPENED.name)
            fee = self.get_fee(self.wallet.url)
            count = float(self.count)-float(fee)
            channel = ch.chose_channel(channels,self.wallet.url.split("@")[0], count, self.asset_type)

            HtlcMessage.create(channel.channel, self.wallet,self.wallet.url, next, count, self.hr,
                               self.tx_nonce, self.role_index,self.asset_type,self.router,
                                   next, comments=self.comments)

    def _handle_1_message(self):
        self.send_responses(self.role_index)
        self.transaction.update_transaction(str(self.tx_nonce), TxType="HTLC", HEDTX=self.hedtx, State="pending")

    def get_fee(self, url):
        router_url = [i[0] for i in self.router]
        index = router_url.index(url)
        try:
            return self.router[index][1]
        except IndexError:
            return 0

    def get_next_router(self):
        router_url = [i[0] for i in self.router]
        index = router_url.index(self.wallet.url)
        try:
            return router_url[index+1]
        except IndexError:
            return None

    @staticmethod
    def create(channel_name, wallet,sender, receiver, HTLCvalue, hashR,tx_nonce, role_index,asset_type,router,
               next_router, comments=None):
        """

        :param channel_name:
        :param wallet:
        :param sender:
        :param receiver:
        :param HTLCvalue:
        :param hashR:
        :param tx_nonce:
        :param role_index:
        :param asset_type:
        :param router:
        :param next_router:
        :param comments:
        :return:
        """
        transaction = TrinityTransaction(channel_name, wallet)
        balance = ch.Channel.channel(channel_name).get_balance()
        print(balance)
        senderpubkey = sender.strip().split("@")[0]
        receiverpubkey = receiver.strip().split("@")[0]
        sender_balance = balance.get(senderpubkey).get(asset_type)
        receiver_balance = balance.get(receiverpubkey).get(asset_type)
        founder = transaction.get_founder()
        if role_index == 0:

            hctx = create_sender_HTLC_TXS(senderpubkey, receiverpubkey, HTLCvalue, sender_balance,
                                      receiver_balance, hashR, founder["originalData"]["addressFunding"],
                                      founder["originalData"]["scriptFunding"])
            transaction.update_transaction(str(tx_nonce), HR=hashR, TxType="HTLC",
                                           Count=HTLCvalue, State="pending")

            hedtx_sign = wallet.SignContent(hctx["HEDTX"]["txData"])
            hedtx = {"txDataSign": hedtx_sign,
                     "originalData": hctx["HEDTX"]}
            hctx["HEDTX"] = hedtx

        elif role_index == 1:
            hctx = create_receiver_HTLC_TXS(senderpubkey, receiverpubkey, HTLCvalue, sender_balance,
                                      receiver_balance, hashR, founder["originalData"]["addressFunding"],
                                      founder["originalData"]["scriptFunding"])

            hetx_sign = wallet.SignContent(hctx["HETX"]["txData"])
            hetx = {"txDataSign": hetx_sign,
                     "originalData": hctx["HETX"]}
            hctx["HETX"] = hetx

            herdtx_sign = wallet.SignContent(hctx["HERDTX"]["txData"])
            herdtx = {"txDataSign": hetx_sign,
                    "originalData": hctx["HERDTX"]}
            hctx["HERDTX"] = herdtx

        else:
            LOG.error("Not correct role index, expect 0/1 but get {}".format(str(role_index)))
            return None

        hctx["RoleIndex"] = role_index
        hctx["Comments"] = comments
        hctx["Count"] = HTLCvalue
        hctx["AssetType"] = asset_type
        hctx["HashR"] = hashR

        message = { "MessageType":"Htlc",
                  "Sender": sender,
                  "Receiver":receiver,
                  "TxNonce": tx_nonce,
                  "ChannelName":channel_name,
                   "Router": router,
                   "Next":next_router,
                  "MessageBody": hctx

        }
        Message.send(message)

        return None

    def _send_0_response(self):
        hctx_sig = {"txDataSign": self.sign_message(self.hctx.get("txData")),
                    "originalData": self.hctx}
        rdtx_sig = {"txDataSign": self.sign_message(self.rdtx.get("txData")),
                    "originalData": self.rdtx}
        httx_sig = {"txDataSign": self.sign_message(self.httx.get("txData")),
                    "originalData": self.httx}
        htrdtx_sig = {"txDataSign": self.sign_message(self.htrdtx.get("txData")),
                      "originalData": self.htrdtx}


        message_response = {"MessageType": "HtlcSign",
                            "Sender": self.receiver,
                            "Receiver": self.sender,
                            "TxNonce": self.tx_nonce,
                            "ChannelName": self.channel_name,
                            "Router": self.router,
                            "MessageBody": {
                                "HCTX": hctx_sig,
                                "RDTX": rdtx_sig,
                                "HTTX": httx_sig,
                                "HTRDTX": htrdtx_sig,
                                "RoleIndex": 0,
                                "Count":self.count,
                                "AssetType": self.asset_type,
                                 "HashR": self.hr
                                }
                            }
        Message.send(message_response)

    def _send_1_response(self):
        hctx_sig = {"txDataSign": self.sign_message(self.hctx.get("txData")),
                    "originalData": self.hctx}
        rdtx_sig = {"txDataSign": self.sign_message(self.rdtx.get("txData")),
                    "originalData": self.rdtx}
        htdtx_sig = {"txDataSign": self.sign_message(self.htdtx.get("txData")),
                    "originalData": self.htdtx}
        message_response = {"MessageType": "HtlcSign",
                            "Sender": self.receiver,
                            "Receiver": self.sender,
                            "TxNonce": self.tx_nonce,
                            "ChannelName": self.channel_name,
                            "Router": self.router,
                            "MessageBody": {
                                "HCTX": hctx_sig,
                                "RDTX": rdtx_sig,
                                "HTDTX": htdtx_sig,
                                "RoleIndex": 1,
                                "Count": self.count,
                                "AssetType": self.asset_type,
                                 "HashR": self.hr
                                 }
                            }
        Message.send(message_response)

    def send_responses(self, role_index, error = None):
        if not error:
            if role_index == 0:
                self._send_0_response()
            elif role_index == 1:
                self._send_1_response()
            else:
                LOG.error("No correct roleindex {}".format(str(role_index)))
        else:
            message_response = { "MessageType":"HtlcFail",
                                "Sender": self.receiver,
                                "Receiver":self.sender,
                                "TxNonce": self.tx_nonce,
                                 "ChannelName": self.channel_name,
                                "MessageBody": self.message_body,
                                "Error": error
                                }
            Message.send(message_response)


class HtlcResponsesMessage(TransactionMessage):
    """
    { "MessageType":"HtlcGSign",
      "Sender": self.receiver,
      "Receiver":self.sender,
      "TxNonce": 0,
      "ChannelName":"090A8E08E0358305035709403",
      "MessageBody": {
                   "Commitment":{}
                   "RevocableDelivery":"
                   "BreachRemedy":""
                    }
    }
    """
    def __init__(self, message, wallet):
        super().__init__(message, wallet)
        self.hctx = self.message_body.get("HCTX")
        self.rdtx = self.message_body.get("RDTX")
        self.hedtx = self.message_body.get("HEDTX")
        self.htdtx = self.message_body.get("HTDTX")
        self.httx = self.message_body.get("HTTX")
        self.htrdtx = self.message_body.get("HTRDTX")
        self.role_index = self.message_body.get("RoleIndex")
        self.channel_name = message.get("ChannelName")
        self.value = self.message_body.get("Value")
        self.comments = self.message_body.get("Comments")
        self.router = self.message.get("Router")
        self.count = self.message_body.get("Count")
        self.asset_type = self.message_body.get("AssetType")
        self.hr = self.message_body.get("HashR")
        self.transaction = TrinityTransaction(self.channel_name, self.wallet)

    def check_if_the_last_router(self):
        return self.wallet.url == self.router[-1][0]

    def handle_message(self):
        if self.error:
            return "{} message error"
        verify, error = self.verify()
        if verify:
            self.transaction.update_transaction(str(self.tx_nonce), HCTX = self.hctx, HEDTX=self.hedtx, HTTX= self.httx)
            if self.role_index ==1:
                if self.check_if_the_last_router():
                    r = Payment(self.wallet).fetch_r(self.hr)
                    RResponse.create(self.wallet.url, self.sender, self.tx_nonce,
                                     self.channel_name, self.hr, r[0], self.count, self.asset_type, self.comments)
                    self.transaction.update_transaction(str(self.tx_nonce), State="confirm")

    def verify(self):
        return True, None


class SettleMessage(TransactionMessage):
    """
    {
    "MessageType":"Settle",
    "Sender": "0x9090909090909090909090909@127.0.0.1:20553",
    "Receiver":"0x101010101001001010100101@127.0.0.1:20552",
    "TxNonce": -1,   # int type
    "ChannelName":"902ae9090232048575",
    "AssetType": "TNC",
    "MessageBody": {
            "Commitment":"",
            "SenderBalance": int(),
            "ReceiverBalance": int()
        }
    }
    """

    def __init__(self, message, wallet):
        super().__init__(message, wallet)

        self.channel = None
        self.channel_name = self.message.get('ChannelName')
        self.asset_type = self.message.get('AssetType', '').strip().upper()

        self.commitment = self.message_body.get('Commitment')
        self.sender_balance = self.message_body.get('SenderBalance')
        self.receiver_balance = self.message_body.get("SenderBalance")

    def handle_message(self):
        self.handle()

    def handle(self):
        super(SettleMessage, self).handle()
        verified, status = self.verify()

        self.channel = ch.Channel.channel(self.channel_name)

        balance = self.channel.get_balance()
        sender_balance = balance.get(self.sender_address).get(self.asset_type)
        receiver_balance = balance.get(self.receiver_balance).get(self.asset_type)

        # To create settle response message
        SettleResponseMessage.create(self.wallet, self.channel_name, self.asset_type, self.sender, self.receiver,
                                     sender_balance, receiver_balance, self.commitment)

        if not verified:
            LOG.error('Error<{}> occurred during verify message.'.format(status))
        else:
            # trigger channel event
            self.channel.update_channel(state=EnumChannelState.SETTLING.name)

            # TODO: monitor event to set channel closed state
            pass

    @staticmethod
    def create(wallet, channel_name, sender, receiver, asset_type):
        """

        :param channel_name:
        :param wallet:
        :param sender:
        :param receiver:
        :param asset_type:
        :return:
        """
        # assert wallet.url == sender, 'Wallet url<{}> is not equal to founder<{}>'.format(wallet.url, sender)
        if wallet.url != sender:
            receiver = sender
            sender = wallet.url

        channel = ch.Channel.channel(channel_name)
        if not channel:
            LOG.error('Channel<{}> not found!'.format(channel_name))
            return

        nonce = 0xFFFFFFFFFFFFFFFF
        asset_type = asset_type.upper()

        sender_addr = sender.split("@")[0].strip()
        receiver_addr = receiver.split("@")[0].strip()

        balance = channel.get_balance()
        sender_balance = balance.get(sender_addr).get(asset_type)
        receiver_balance = balance.get(receiver_addr).get(asset_type)

        commitment = SettleMessage.sign_content(
            typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
            valueList=[channel_name, nonce, sender_addr, sender_balance, receiver_addr, receiver_balance],
            privtKey = wallet._key.private_key_string)

        message = {
            "MessageType":"Settle",
            "Sender": sender,
            "Receiver": receiver,
            "TxNonce": nonce,
            "ChannelName": channel_name,
            "AssetType": asset_type,
            "MessageBody": {
                "Commitment": commitment,
                "SenderBalance": sender_balance,
                "ReceiverBalance": receiver_balance
            }
        }
        Message.send(message)

        # update channel
        channel.update_channel(state=EnumChannelState.SETTLING.name)
        ch.Channel.add_trade(channel_name,
                             nonce = nonce,
                             type = EnumTradeType.TRADE_TYPE_SETTLE.value,
                             role = EnumTradeRole.TRADE_ROLE_FOUNDER,
                             payment = 0,
                             address = sender,
                             balance = {asset_type: sender_balance},
                             commitment = commitment,
                             peer = receiver,
                             peer_balance = {asset_type: receiver_balance},
                             peer_commitment = None,
                             state = EnumTradeState.confirming)

    def verify(self):
        return True, EnumResponseStatus.RESPONSE_OK


class SettleResponseMessage(TransactionMessage):
    """
    {
        "MessageType":"SettleSign",
        "Sender": "0x9090909090909090909090909@127.0.0.1:20553",
        "Receiver":"0x101010101001001010100101@127.0.0.1:20552",
        "TxNonce": -1,   # int type
        "ChannelName":"902ae9090232048575",
        "AssetType": "TNC",
        "MessageBody": {
                "Commitment":"",
            }
        "Status": RESPONSE_OK
    }
    """

    def __init__(self, message, wallet):
        super().__init__(message, wallet)

        self.channel = None
        self.channel_name = self.message.get('ChannelName')
        self.asset_type = self.message.get('AssetType', '').strip().upper()
        self.status = self.message.get('Status')
        self.peer_commitment = self.message_body.get('Commitment')

        self.wallet = wallet

    def handle_message(self):
        self.handle()

    def handle(self):
        super(SettleResponseMessage, self).handle()
        nonce = 0xFFFFFFFFFFFFFFFF

        verified, status = self.verify()
        if verified:
            # get channel info
            self.channel = ch.Channel.channel(self.channel_name)

            # update transaction
            self.channel.update_trade(self.channel_name, nonce, peer_commit = self.peer_commitment)

            try:
                settle = self.channel.query_trade(self.channel_name, nonce=nonce)[0]
            except Exception as error:
                LOG('Transaction with none<0xFFFFFFFFFFFFFFFF> not found. Error: {}'.format(error))
            else:
                # call web3 interface to trigger transaction to on-chain
                # quick_settle(invoker, channel_id, nonce, founder, founder_balance,
                #              partner, partner_balance, founder_signature, partner_signature, invoker_key)
                SettleResponseMessage.quick_settle(settle.address, self.channel_name, nonce,
                                                settle.address, settle.balance.get(self.asset_type),
                                                settle.peer, settle.peer_commitment.get(self.asset_type),
                                                settle.commitment, settle.peer_commitment,
                                                self.wallet._key.private_key_string)

                # TODO: register monitor event to set channel closed
                pass
        else:
            LOG.error('Error<{}> occurred during verified the message<{}>.'.format(status, self.message_type))

    def verify(self):
        if self.status not in EnumResponseStatus.RESPONSE_OK.__dict__.values():
            return False, self.status

        return True, None

    @staticmethod
    def create(wallet, channel_name, asset_type, sender, receiver, sender_balance, receiver_balance, commitment):
        """

        :param wallet:
        :param channel_name:
        :param asset_type:
        :param sender:
        :param receiver:
        :param sender_balance:
        :param receiver_balance:
        :param commitment:
        :param status:
        :return:
        """
        status = EnumResponseStatus.RESPONSE_OK
        sender_addr = sender.split("@")[0].strip()
        receiver_addr = receiver.split("@")[0].strip()
        trade_state = EnumTradeState.confirmed
        nonce = 0xFFFFFFFFFFFFFFFF
        message = {
            "MessageType":"SettleSign",
            "Sender": receiver,
            "Receiver": sender,
            "TxNonce": nonce,   # int type
            "ChannelName": channel_name,
            "AssetType": asset_type,
        }

        try:
            self_commitment = SettleMessage.sign_content(
                typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
                valueList=[channel_name, nonce, sender_addr, sender_balance, receiver_addr, receiver_balance],
                privtKey = wallet._key.private_key_string)
        except EnumChannelState as error:
            LOG.error('Error occurred during create Settle response. Error: {}'.format(error))
            status = EnumResponseStatus.RESPONSE_FAIL

        message.update({"MessageBody": {"Commitment": self_commitment}})
        message.update({'Status': status.name})
        Message.send(message)

        # add trade
        ch.Channel.add_trade(channel_name,
                             nonce = nonce,
                             type = EnumTradeType.TRADE_TYPE_SETTLE.value,
                             role = EnumTradeRole.TRADE_ROLE_PARTNER,
                             payment = 0,
                             address = receiver,
                             balance = {asset_type: receiver_balance},
                             commitment = self_commitment,
                             peer = sender,
                             peer_balance = {asset_type: sender_balance},
                             peer_commitment = commitment,
                             state = trade_state.name)
        ch.Channel.update_channel(channel_name, state=EnumChannelState.SETTLING.name)
        # TODO: register monitor event to set channel closed
        pass


class PaymentLink(TransactionMessage):
    """
    {
        "MessageType": "PaymentLink",
        "Sender": "03dc2841ddfb8c2afef94296693315a234026fa8f058c3e4259a04f8be6d540049@106.15.91.150:8089",
        "MessageBody": {
            "Parameter": {
                "Amount": 0,
                "Assets": "TNC",
                "Description": "Description"
            }
        }
    }"""

    def __init__(self, message, wallet):
        super().__init__(message, wallet)

        parameter = self.message_body.get("Parameter")
        self.amount = parameter.get("Amount") if parameter else None
        self.asset = parameter.get("Assets") if parameter else None
        self.comments = parameter.get("Description") if parameter else None

    def handle_message(self):
        pycode = Payment(self.wallet,self.sender).generate_payment_code(get_asset_type_id(self.asset),
                         self.amount, self.comments)
        message = {"MessageType":"PaymentLinkAck",
                   "Receiver":self.sender,
                   "MessageBody": {
                                    "PaymentLink": pycode
                                   },
                   }
        Message.send(message)

        return None


class PaymentAck(TransactionMessage):
    """
        {
        "MessageType": "PaymentAck",
        "Receiver": "03dc2841ddfb8c2afef94296693315a234026fa8f058c3e4259a04f8be6d540049@106.15.91.150:8089",
        "MessageBody": {
            "State": "Success",
            "Hr": "Hr"
        }
    }
    """
    def __init__(self,message, wallet):
        super().__init__(message, wallet)

    @staticmethod
    def create(receiver, hr, state="Success"):
        message = {
        "MessageType": "PaymentAck",
        "Receiver": receiver,
        "MessageBody": {
                         "State": state,
                         "Hr": hr
                         }
                }
        Message.send(message)


def monitor_founding(height, channel_name, state):
    channel = ch.Channel.channel(channel_name)
    deposit = channel.get_deposit()
    channel.update_channel(state=state, balance = deposit)
    ch.sync_channel_info_to_gateway(channel_name,"AddChannel")
    print("Channel is {}".format(state))
    return None


def monitor_height(height, txdata, signother, signself):
    register_block(str(int(height)+1000),send_rsmcr_transaction,height,txdata,signother, signself)


def send_rsmcr_transaction(height,txdata,signother, signself):
    height_script = blockheight_to_script(height)
    rawdata = txdata.format(blockheight_script=height_script,signOther=signother,signSelf=signself)
    TrinityTransaction.sendrawtransaction(rawdata)
