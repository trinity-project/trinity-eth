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
from .message import TransactionBase
from .response import EnumResponseStatus
from .rsmc import RsmcMessage
from wallet.channel import Payment

from blockchain.interface import get_block_count
from common.log import LOG
from common.console import console_log
from common.number import TrinityNumber
from common.common import uri_parser
from common.exceptions import GoTo, TrinityException
from wallet.channel import Channel
from model.channel_model import EnumChannelState
from wallet.channel import EnumTradeType, EnumTradeRole, EnumTradeState
from wallet.event.event import EnumEventAction, event_machine
import json


class RResponse(TransactionBase):
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
    _message_name = 'RResponse'

    def __init__(self,message, wallet):
        super(RResponse, self).__init__(message)

        self.hashcode = self.message_body.get("HashR")
        self.rcode = self.message_body.get("R")
        self.payment = self.message_body.get('PaymentCount')

        self.wallet = wallet

    @staticmethod
    def create(channel_name, asset_type, nonce, sender, receiver, hashcode, rcode, comments=None):
        """

        :param channel_name:
        :param asset_type:
        :param nonce:
        :param sender:
        :param receiver:
        :param hashcode:
        :param value:
        :param comments:
        :return:
        """
        htlc_trade = RResponse.get_htlc_trade_by_hashr(channel_name, hashcode)
        asset_type = asset_type.upper()
        payer_address, _, _ = uri_parser(receiver)
        payment = htlc_trade.hlock.get(payer_address).get(asset_type)

        message = RResponse.create_message_header(sender, receiver, RResponse._message_name,
                                                  channel_name, asset_type, nonce)
        message = message.message_header

        message_body = {
            "HashR": hashcode,
            "R": rcode,
            "PaymentCount": payment,
        }

        message.update({'MessageBody': message_body})

        if comments:
            message.update({'Comments': comments})

        RResponse.send(message)

    def handle_message(self):
        self.handle()

    def handle(self):
        super(RResponse, self).handle()

        status = EnumResponseStatus.RESPONSE_OK
        try:
            self.check_channel_state(self.channel_name)
            self.check_rcode(self.hashcode, self.rcode)

            htlc_trade = self.get_htlc_trade_by_hashr(self.channel_name, self.hashcode)
            Channel.update_trade(self.channel_name, htlc_trade.nonce, rcode=self.rcode)
            # check payment:
            stored_payment = htlc_trade.get(self.receiver_address).get(self.asset_type)
            if stored_payment != self.payment:
                raise GoTo(EnumResponseStatus.RESPONSE_TRADE_UNMATCHED_PAYMENT,
                           'Unmatched payment. self stored payment<{}>, peer payment<{}>'.format(stored_payment,
                                                                                                 self.payment))

            # send response OK message
            RResponseAck.create(self.channel_name, self.asset_type, self.nonce, self.sender, self.receiver,
                                self.hashcode, self.rcode, self.payment, self.comments, status)

            # trigger rsmc
            self.trigger_pay_by_rsmc()

            # notify rcode to next peer
            self.notify_rcode_to_next_peer(htlc_trade.channel)
        except TrinityException as error:
            LOG.error(error)
            status = error.reason
        except Exception as error:
            status = EnumResponseStatus.RESPONSE_EXCEPTION_HAPPENED
            LOG.error('Failed to handle RResponse with HashR<{}>. Exception: {}'.format(self.hashcode, error))
            pass
        finally:
            if EnumResponseStatus.RESPONSE_OK != status:
                RResponseAck.send_error_response(self.sender, self.receiver, self.channel_name, self.asset_type,
                                                 self.nonce, status)

        return None

    def trigger_pay_by_rsmc(self):
        try:
            # change htlc to rsmc
            RsmcMessage.create(self.channel_name, self.asset_type, self.wallet.url, self.sender, self.payment,
                               self.hashcode, comments=self.comments)
        except Exception as error:
            LOG.error('Failed to pay from htlc<{}> to rsmc. Need timer to handle later.'.format(self.hashcode))

        return

    def notify_rcode_to_next_peer(self, next_channel):
        """

        :param next_channel:
        :return:
        """
        peer = None
        try:
            # original payer is found
            if not next_channel:
                LOG.info('HTLC Founder with HashR<{}> received the R-code<{}>'.format(self.hashcode, self.rcode))
                return

            # notify the previous node the R-code
            LOG.debug('Payment get channel {}/{}'.format(next_channel, self.hashcode))
            channel = Channel(next_channel)
            peer = channel.peer_uri(self.wallet.url)
            nonce = channel.latest_nonce(next_channel)
            LOG.info("Next peer: {}".format(peer))
            self.create(next_channel, self.asset_type, nonce, self.wallet.url, peer,
                        self.hashcode, self.rcode, self.comments)
        except Exception as error:
            LOG.error('Failed to notify RCode<{}> to peer<{}>'.format(self.rcode, peer))


class RResponseAck(TransactionBase):
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
    _message_name = 'RResponseAck'
    def __init__(self, message, wallet):
        super().__init__(message)
        self.wallet =wallet

    def handle_message(self):
        super(RResponseAck, self).handle()
        # print(json.dumps(self.message, indent=4))

    @staticmethod
    def create(channel_name, asset_type, nonce, sender, receiver, hashcode, rcode, payment, comments='',
               status=EnumResponseStatus.RESPONSE_OK):
        """

        :param sender:
        :param receiver:
        :param channel_name:
        :param nonce:
        :param asset_type:
        :param hashcode:
        :param rcode:
        :param payment:
        :param comments:
        :param status:
        :return:
        """
        message = RResponseAck.create_message_header(receiver, sender, RResponseAck._message_name,
                                                     channel_name, asset_type.upper(), nonce)
        message = message.message_header

        message_body = {
            "HashR": hashcode,
            "R": rcode,
            "PaymentCount": payment,
        }

        message.update({'MessageBody': message_body})

        if comments:
            message.update({'Comments': comments})

        if status:
            message.update({'Status': status.name})

        RResponseAck.send(message)


class HtlcBase(TransactionBase):
    """

    """
    def __init__(self, message, wallet):
        super().__init__(message)

        self.sender_balance = self.message_body.get('SenderBalance')
        self.receiver_balance = self.message_body.get('ReceiverBalance')
        self.payment = self.message_body.get('Payment')
        self.commitment = self.message_body.get('Commitment')

        self.delay_block = self.message_body.get('DelayBlock')
        self.delay_commitment = self.message_body.get('DelayCommitment')
        self.hashcode = self.message_body.get('HashR')

        self.router = message.get('Router', [])
        self.next_router = message.get('Next', None)
        self.wallet = wallet

    def check_if_the_last_router(self):
        return self.wallet.url in self.router[-1]

    @classmethod
    def check_router(self, router, hashcode):
        if not router:
            raise GoTo(EnumResponseStatus.RESPONSE_ROUTER_VOID_ROUTER,
                       'Router<{}> NOT found for htlc trade with HashR<{}>'.format(router, hashcode))

        return True


class HtlcMessage(HtlcBase):
    """
    { "MessageType":"Htlc",
    "Sender": "9090909090909090909090909@127.0.0.1:20553",
    "Receiver":"101010101001001010100101@127.0.0.1:20552",
    "TxNonce": 0,
    "ChannelName":"3333333333333333333333333333",
    "Router":[],
    "Next":"",
    "MessageBody": {
        'SenderBalance': sender_balance,
        'ReceiverBalance': receiver_balance,
        'Commitment': conclusive_commitment,
        'Payment': payment,
        'DelayBlock': end_block_height,
        'DelayCommitment': inconclusive_commitment,
        'HashR': hashcode
        }
    }
    """
    _message_name = 'Htlc'
    _block_per_day = 5760 # 4 * 60 * 24: one block per minute.

    def handle_message(self):
        self.handle()

    def handle(self):
        super(HtlcMessage, self).handle()

        status = EnumResponseStatus.RESPONSE_OK
        try:
            self.check_channel_state(self.channel_name)
            self.check_router(self.router, self.hashcode)
            self.verify()
            _, nonce = self.check_nonce(self.nonce, self.channel_name)
            _, payer_balance, payee_balance = self.check_balance(
                self.channel_name, self.asset_type, self.sender_address, self.sender_balance,
                self.receiver_address, self.receiver_balance, is_htcl_type=True)

            # transform the message to the next router if not last router node
            next_router = self.next_router
            if not self.check_if_the_last_router():
                next_router = self.get_next_router()
                LOG.debug('Get Next Router {}'.format(str(next_router)))

                # to get channel
                channel_set = Channel.get_channel(self.wallet.url, next_router, state=EnumChannelState.OPENED)
                if not (channel_set and channel_set[0]):
                    status = EnumResponseStatus.RESPONSE_CHANNEL_NOT_FOUND
                    raise GoTo(EnumResponseStatus.RESPONSE_CHANNEL_NOT_FOUND,
                               'No OPENED channel is found between {} and {}.'.format(self.wallet.url, next_router))
                channel_set = channel_set[0]

                # calculate fee and transfer to next jump
                fee = TrinityNumber(str(self.get_fee(self.wallet.url))).number
                payment = self.big_number_calculate(self.payment, fee, False)
                receiver = next_router
                self.create(self.wallet, channel_set.channel, self.asset_type, self.wallet.url, receiver,
                            payment, self.hashcode, self.router, next_router, self.comments)
            else:
                Channel.update_payment(self.channel_name, self.hashcode)
                payment_trade = Channel.query_payment(self.channel_name, self.hashcode)

                # trigger RResponse
                RResponse.create(self.channel_name, self.asset_type, self.nonce, self.wallet.url, self.sender,
                                 self.hashcode, payment_trade.rcode, self.comments)

            # send response to receiver
            HtlcResponsesMessage.create(self.wallet, self.channel_name, self.asset_type, nonce, self.sender,
                                        self.receiver, self.payment, self.sender_balance, self.receiver_balance,
                                        self.hashcode, self.delay_block, self.commitment,
                                        self.delay_commitment, self.router, next_router, self.comments)

            # update the channel balance
            self.update_balance_for_channel(self.channel_name, self.asset_type, self.sender_address,
                                            self.receiver_address, self.payment, is_htlc_type=True)
        except GoTo as error:
            LOG.error(error)
            status = error.reason
        except Exception as error:
            LOG.error('Failed to handle Htlc message for channel<{}>, HashR<{}>. Exception:{}'.format(self.channel_name,
                                                                                                      self.hashcode,
                                                                                                      error))
            status = EnumResponseStatus.RESPONSE_EXCEPTION_HAPPENED
        finally:
            # failed operation
            if EnumResponseStatus.RESPONSE_OK != status:
                # send error response
                HtlcResponsesMessage.send_error_response(self.sender, self.receiver, self.channel_name,
                                                         self.asset_type, self.nonce, status)

                # delete some related resources
                self.rollback_resource(self.channel_name, self.nonce, self.payment, self.status)

        return

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

    @classmethod
    def get_locked_block_height(cls, total_routers, jumps):
        """

        :param total_routers:
        :param jumps:
        :return:
        """
        if not (isinstance(jumps, int) and isinstance(total_routers, int)):
            return 0

        locked_block_height = get_block_count() + HtlcMessage._block_per_day*(total_routers-jumps)

        return locked_block_height

    @classmethod
    def create(cls, wallet, channel_name, asset_type, sender, receiver, payment, hashcode,
               router, next_router, comments=None):
        """

        :param channel_name:
        :param wallet:
        :param sender:
        :param receiver:
        :param asset_type:
        :param payment:
        :param nonce:
        :param hashcode:
        :param router:
        :param next_router:
        :param comments:
        :return:
        """
        cls.check_channel_state(channel_name)
        cls.check_router(router, hashcode)
        cls.check_asset_type(asset_type)
        cls.check_both_urls(sender, receiver)
        cls.check_router(router, hashcode)

        # get nonce
        nonce = Channel.new_nonce(channel_name)
        if HtlcMessage._FOUNDER_NONCE > nonce:
            raise GoTo(EnumResponseStatus.RESPONSE_TRADE_WITH_INCORRECT_NONCE,
                       'HtlcMessage::create: Incorrect nonce<{}> for channel<{}>'.format(nonce, channel_name))

        # get sender & receiver address from sender or receiver
        payer_address, _, _ = uri_parser(sender)
        payee_address, _, _ = uri_parser(receiver)
        asset_type = asset_type.upper()

        # check whether the balance is enough or not
        channel = Channel(channel_name)
        balance = channel.balance
        _, payer_balance, payee_balance = HtlcMessage.calculate_balance_after_payment(
            balance.get(payer_address, {}).get(asset_type), balance.get(payee_address, {}).get(asset_type), payment,
            is_htlc_type=True
        )

        # calculate the end block height
        jumps_index = HtlcMessage.this_jump(sender, router)
        end_block_height = cls.get_locked_block_height(len(router), jumps_index)

        # Htlc is made up of 2 parts: rsmc and hlock part
        sign_hashcode, sign_rcode = cls.get_default_rcode()
        rsmc_commitment = HtlcMessage.sign_content(
            typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256', 'bytes32', 'bytes32'],
            valueList=[channel_name, nonce, payer_address, payer_balance, payee_address, payee_balance,
                       sign_hashcode, sign_rcode],
            privtKey = wallet._key.private_key_string)

        # hlock parts
        hlock_commitment = HtlcMessage.sign_content(
            start=5,
            typeList=['bytes32', 'uint256', 'address', 'address', 'uint256', 'uint256', 'bytes32'],
            valueList=[channel_name, nonce, payer_address, payee_address, end_block_height, int(payment), hashcode],
            privtKey = wallet._key.private_key_string)

        # # add trade to database
        htlc_trade = Channel.htlc_trade(
            type=EnumTradeType.TRADE_TYPE_HTLC, role=EnumTradeRole.TRADE_ROLE_FOUNDER, asset_type=asset_type,
            balance=payer_balance, peer_balance=payee_balance, payment=payment, hashcode=hashcode, delay_block=end_block_height,
            commitment=rsmc_commitment, delay_commitment=hlock_commitment
        )
        Channel.add_trade(channel_name, nonce=nonce, **htlc_trade)

        # generate the messages
        message_body = {
            'SenderBalance': payer_balance,
            'ReceiverBalance': payee_balance,
            'Commitment': rsmc_commitment,
            'Payment': payment,
            'DelayBlock': end_block_height,
            'DelayCommitment': hlock_commitment,
            'HashR': hashcode
        }

        message = HtlcMessage.create_message_header(sender, receiver, HtlcMessage._message_name,
                                                    channel_name, asset_type, nonce)
        message = message.message_header
        message.update({'Router': router, 'Next': next_router,})
        message.update({'MessageBody': message_body})

        if comments:
            message.update({'Comments': comments})

        HtlcMessage.send(message)

        return None

    @classmethod
    def this_jump(cls, sender, router=[]):
        for jumps in router:
            if sender in jumps:
                return router.index(jumps)

        return None


class HtlcResponsesMessage(HtlcBase):
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
    _message_name = 'HtlcSign'

    def check_if_the_last_router(self):
        return self.wallet.url == self.router[-1][0]

    def handle_message(self):
        self.handle()

    def handle(self):
        super(HtlcResponsesMessage, self).handle()
        nonce = Channel.latest_nonce(self.channel_name)

        try:
            # check the response status
            if not self.check_response_status(self.status):
                return

            self.check_channel_state(self.channel_name)
            self.check_router(self.router, self.hashcode)
            self.verify()
            _, nonce = self.check_nonce(self.nonce, self.channel_name)
            _, payer_balance, payee_balance = self.check_balance(
                self.channel_name, self.asset_type, self.sender_address, self.sender_balance,
                self.receiver_address, self.receiver_balance, is_htcl_type=True)

            # update transaction
            Channel.update_trade(self.channel_name, int(self.nonce), peer_commitment=self.commitment,
                                 peer_delay_commitment=self.delay_commitment)

            # update the channel balance
            self.update_balance_for_channel(self.channel_name, self.asset_type, self.receiver_address,
                                            self.sender_address, self.payment, is_htlc_type=True)
        except GoTo as error:
            LOG.error(error)
        except Exception as error:
            LOG.error('Transaction with none<{}> not found. Error: {}'.format(self.nonce, error))
        else:
            # successful action
            LOG.debug('Succeed to htlc for channel<{}>'.format(self.channel_name))
            return
        finally:
            # rollback the resources
            self.rollback_resource(self.channel_name, nonce, status=self.status)


    @classmethod
    def create(cls, wallet, channel_name, asset_type, tx_nonce, sender, receiver, payment, sender_balance, receiver_balance,
               hashcode, delay_block, peer_commitment, peer_hlock_commitment, router, next_router, comments=None):
        """

        :param channel_name:
        :param wallet:
        :param sender:
        :param receiver:
        :param asset_type:
        :param payment:
        :param tx_nonce:
        :param hashcode:
        :param delay_block:
        :param peer_commitment:
        :param peer_hlock_commitment:
        :param router:
        :param next_router:
        :param comments:
        :return:
        """
        # get nonce from latest trade
        _, nonce = HtlcResponsesMessage.check_nonce(channel_name, tx_nonce)

        # start to verify balance
        payer_address, _, _ = uri_parser(sender)
        payee_address, _, _ = uri_parser(receiver)
        asset_type = asset_type.upper()

        # check balance
        _, payer_balance, payee_balance = HtlcResponsesMessage.check_balance(
            channel_name, asset_type, payer_address, sender_balance, payee_address, receiver_balance,
            is_htcl_type=True, payment=payment )

        # 2 parts in htlc message: conclusive and inconclusive part
        sign_hashcode, sign_rcode = cls.get_default_rcode()
        rsmc_commitment = HtlcResponsesMessage.sign_content(
            typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256', 'bytes32', 'bytes32'],
            valueList=[channel_name, nonce, payer_address, payer_balance, payee_address, payee_balance,
                       sign_hashcode, sign_rcode],
            privtKey = wallet._key.private_key_string)

        hlock_commitment = HtlcResponsesMessage.sign_content(
            start=5,
            typeList=['bytes32', 'uint256', 'address', 'address', 'uint256', 'uint256', 'bytes32'],
            valueList=[channel_name, nonce, payer_address, payee_address, delay_block, int(payment), hashcode],
            privtKey = wallet._key.private_key_string)

        # # ToDo: need re-sign all unconfirmed htlc message later
        htlc_trade = Channel.htlc_trade(
            type=EnumTradeType.TRADE_TYPE_HTLC, role=EnumTradeRole.TRADE_ROLE_PARTNER, asset_type=asset_type,
            balance=payee_balance, peer_balance=payer_balance, payment=payment, hashcode=hashcode,
            delay_block=delay_block, commitment=rsmc_commitment, peer_commitment=peer_commitment,
            delay_commitment=hlock_commitment, peer_delay_commitment=peer_hlock_commitment, channel=channel_name)
        Channel.add_trade(channel_name, nonce=nonce, **htlc_trade)

        # create message
        message = HtlcResponsesMessage.create_message_header(receiver, sender, HtlcResponsesMessage._message_name,
                                                             channel_name, asset_type, tx_nonce)
        message = message.message_header
        message.update({'Router': router, 'Next': next_router,})
        message_body = {
            'SenderBalance': payer_balance,
            'ReceiverBalance': payee_balance,
            'Commitment': rsmc_commitment,
            'Payment': payment,
            'DelayBlock': delay_block,
            'DelayCommitment': hlock_commitment,
            'HashR': hashcode
        }

        # orgnize the message
        message.update({'MessageBody': message_body})
        message.update({'Status': EnumResponseStatus.RESPONSE_OK.name})
        if comments:
            message.update({'Comments': comments})

        HtlcResponsesMessage.send(message)

        return
