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
from .message import Message
from .response import EnumResponseStatus
from .rsmc import RsmcMessage
from .payment import Payment

from blockchain.interface import get_block_count
from common.log import LOG
from common.console import console_log
from common.common import uri_parser
from common.exceptions import GoTo, GotoIgnore
from wallet.channel import Channel
from wallet.channel import EnumTradeType, EnumTradeRole, EnumTradeState
from wallet.event.contract_event import contract_event_api
from model.channel_model import EnumChannelState
from wallet.channel import EnumTradeType, EnumTradeRole, EnumTradeState
from wallet.event.event import EnumEventAction, event_machine
import json


class RResponse(Message):
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
        self.r = self.message_body.get("R")
        self.payment = self.message_body.get('PaymentCount')

        self.wallet = wallet

    @staticmethod
    def create(sender, receiver, nonce, channel_name, hr, r, value, asset_type, comments):
        """

        :param sender:
        :param receiver:
        :param nonce:
        :param channel_name:
        :param hr:
        :param r:
        :param value:
        :param asset_type:
        :param comments:
        :return:
        """
        message = RResponse.create_message_header(sender, receiver, RResponse._message_name,
                                                  channel_name, asset_type.upper(), nonce)
        message = message.message_header

        message_body = {
            "HashR": hr,
            "R": r,
            "PaymentCount": value,
        }

        message.update({'MessageBody': message_body})

        if comments:
            message.update({'Comments': comments})

        Message.send(message)

    def verify(self):
        if self.receiver != self.wallet.url:
            return False, "Not Send to me"

        # if not Payment.verify_hr(self.hashcode, self.r):
        #     return False, 'Incorrect HashR<{}>'.format(self.hashcode)

        return True, None

    def handle_message(self):
        self.handle()

    def handle(self):
        super(RResponse, self).handle()

        status = EnumResponseStatus.RESPONSE_OK
        try:
            verified, error = self.verify()

            if not verified:
                status = EnumResponseStatus.RESPONSE_TRADE_VERIFIED_ERROR
                raise GoTo('{}'.format(error))

            # get payment record from db
            payment_hash = Channel.query_payment(self.channel_name, hashcode=self.hashcode)
            if not (payment_hash and payment_hash[0]):
                status = EnumResponseStatus.RESPONSE_TRADE_HASHR_NOT_FOUND
                raise GoTo('HashR<{}> not found int DB'.format(self.hashcode))
            payment_hash = payment_hash[0]
            channel_name = payment_hash.channel

            # make up RSMC message after the database is already gotten
            RsmcMessage.create(self.channel_name, self.wallet, self.wallet.url, self.sender, self.payment,
                               self.asset_type, comments=self.hashcode)

            if channel_name == self.channel_name:
                raise GotoIgnore('Sender received the R-code<{}>'.format(self.r))

            # notify the previous node the R-code
            LOG.debug('Payment get channel {}/{}'.format(payment_hash.hashcode, channel_name))
            payment = payment_hash.payment
            channel = Channel(channel_name)
            peer = channel.peer_uri(self.wallet.url)
            LOG.info("Next peer url: {}".format(peer))
            self.create(self.wallet.url, peer, self.nonce, channel_name, self.hashcode, self.r,
                        payment, self.asset_type, self.comments)

        except GoTo as error:
            LOG.error(error)
        except GotoIgnore as info:
            LOG.info(info)
        except Exception as error:
            status = EnumResponseStatus.RESPONSE_EXCEPTION_HAPPENED
            LOG.exception('Failed to handle RResponse with HashR<{}>. Exception: {}'.format(self.hashcode, error))
            pass
        finally:
            RResponseAck.create(self.sender, self.receiver, self.channel_name, self.nonce, self.asset_type,
                                self.hashcode, self.r, self.payment, self.comments, status=status)

        return None


class RResponseAck(Message):
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
    def create(sender, receiver, channel_name, nonce, asset_type, hashcode, r, payment, comments='',
               status=EnumResponseStatus.RESPONSE_OK):
        """

        :param sender:
        :param receiver:
        :param channel_name:
        :param nonce:
        :param asset_type:
        :param hashcode:
        :param r:
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
            "R": r,
            "PaymentCount": payment,
        }

        message.update({'MessageBody': message_body})

        if comments:
            message.update({'Comments': comments})

        if status:
            message.update({'Status': status.name})

        Message.send(message)


class HtlcMessage(Message):
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

    def __init__(self, message, wallet):
        super().__init__(message)

        self.router = message.get('Router', [])
        self.next_router = message.get('Next', None)

        self.sender_balance = self.message_body.get('SenderBalance')
        self.receiver_balance = self.message_body.get('ReceiverBalance')
        self.commitment = self.message_body.get('Commitment')
        self.payment = self.message_body.get('Payment')
        self.delay_block = self.message_body.get('DelayBlock')
        self.delay_commitment = self.message_body.get('DelayCommitment')
        self.hashcode = self.message_body.get('HashR')

        self.channel = Channel(self.channel_name)
        self.wallet = wallet

    def handle_message(self):
        self.handle()

    def verify(self):
        verified, error = super(HtlcMessage, self).verify()
        if not verified:
            return verified, error

        return True, None

    def check_if_the_last_router(self):
        return self.wallet.url in self.router[-1]

    def handle(self):
        super(HtlcMessage, self).handle()

        try:
            verified, error = self.verify()
            if not verified:
                raise GoTo('Htlc verified error: {}'.format(error))

            # transform the message to the next router if not last router node
            next_router = self.next_router
            if not self.check_if_the_last_router():
                next_router = self.get_next_router()
                LOG.debug('Get Next Router {}'.format(str(next_router)))

                # to get channel
                channel_set = Channel.get_channel(self.wallet.url, next_router, state=EnumChannelState.OPENED)
                if not (channel_set and channel_set[0]):
                    raise GoTo('No OPENED channel is found between {} and {}.'.format(self.wallet.url,
                                                                                      next_router))
                channel_set = channel_set[0]

                # calculate
                fee = self.get_fee(self.wallet.url)
                payment = self.float_calculate(self.payment, fee, False)
                receiver = next_router
                HtlcMessage.create(channel_set.channel, self.wallet, self.wallet.url, receiver, self.asset_type,
                                   payment, self.hashcode, self.router, next_router)
            else:
                payment_hash = Channel.query_payment(self.channel_name, hashcode=self.hashcode)
                if not(payment_hash and payment_hash[0]):
                    raise GoTo('Not found the HashR<{}>. Exception: {}'.format(self.hashcode, error))
                payment_hash = payment_hash[0]

                # trigger RResponse
                RResponse.create(self.wallet.url, self.sender, self.nonce, self.channel_name,
                                 self.hashcode, payment_hash.rcode, self.payment, self.asset_type, self.comments)

        except GoTo as error:
            LOG.error(error)
        except Exception as error:
            LOG.exception('Failed to handle Htlc message for channel<{}>, HashR<{}>. Exception:{}'.format(self.channel_name,
                                                                                                      self.hashcode,
                                                                                                      error))
        else:
            # send response to receiver
            HtlcResponsesMessage.create(self.channel_name, self.wallet, self.sender, self.receiver, self.asset_type,
                                        self.payment, self.nonce, self.hashcode, self.delay_block,
                                        self.commitment, self.delay_commitment, self.router, next_router)

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

    @staticmethod
    def create(channel_name, wallet, sender, receiver, asset_type, payment, hashcode,
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
        channel = Channel(channel_name)

        latest_trade = channel.latest_trade(channel_name)
        if not latest_trade:
            LOG.error('No trade records in this channel<{}>'.format(channel_name))
            return
        nonce = int(latest_trade.nonce) + 1

        try:
            message = HtlcMessage.create_message_header(sender, receiver, HtlcMessage._message_name,
                                                        channel_name, asset_type, nonce)
            message = message.message_header
            message.update({'Router': router, 'Next': next_router,})
        except Exception as error:
            LOG.error('Failed to create HTLC message. Exception: {}'.format(error))
            return
        else:
            sender_address, _, _ = uri_parser(sender)
            receiver_address, _, _ = uri_parser(receiver)
            asset_type = asset_type.upper()

            balance = channel.balance
            console_log.info(balance)
            sender_balance = float(balance.get(sender_address, {}).get(asset_type, 0))
            assert sender_balance >= payment, 'No enough balance<{}> for payment<{}>'.format(sender_balance, payment)

            sender_balance = HtlcMessage.float_calculate(sender_balance, payment, False)
            sender_locked_balance = payment
            receiver_balance = balance.get(receiver_address, {}).get(asset_type, 0)

            # 2 parts in htlc message: conclusive and inconclusive part
            # ToDo:
            conclusive_commitment = contract_event_api.sign_content(
                typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
                valueList=[channel_name, nonce, sender_address, sender_balance, receiver_address, receiver_balance],
                privtKey = wallet._key.private_key_string)

            if router:
                jumps_index = HtlcMessage.this_point(sender, router)
                if jumps_index is not None:
                    end_block_height = get_block_count() + HtlcMessage._block_per_day*(len(router)-jumps_index)
                else:
                    end_block_height = 0
            else:
                LOG.error('Router<{}> should not be void.'.format(router))
                return

            inconclusive_commitment = contract_event_api.sign_content(
                start=5,
                typeList=['bytes32', 'uint256', 'address', 'address', 'uint256', 'uint256', 'bytes32'],
                valueList=[channel_name, nonce, sender_address, receiver_address,
                           end_block_height, sender_locked_balance, hashcode],
                privtKey = wallet._key.private_key_string)

            message_body = {
                'SenderBalance': sender_balance,
                'ReceiverBalance': receiver_balance,
                'Commitment': conclusive_commitment,
                'Payment': payment,
                'DelayBlock': end_block_height,
                'DelayCommitment': inconclusive_commitment,
                'HashR': hashcode
            }
            message.update({'MessageBody': message_body})

            if comments:
                message.update({'Comments': comments})

            Message.send(message)

            # # add trade to database
            # # ToDo: need re-sign all unconfirmed htlc message later
            rsmc_trade = Channel.founder_or_rsmc_trade(
                role=EnumTradeRole.TRADE_ROLE_FOUNDER, asset_type=asset_type, payment=0,
                balance=sender_balance, peer_balance=receiver_balance,
                commitment=conclusive_commitment, peer_commitment=None, state=EnumTradeState.confirming
            )
            htlc_trade = Channel.htlc_trade(
                role=EnumTradeRole.TRADE_ROLE_FOUNDER, asset_type=asset_type,
                hashcode=hashcode, rcode=None, payment=payment, delay_block=end_block_height,
                commitment=inconclusive_commitment, peer_commitment=None, state=EnumTradeState.confirming)

            Channel.add_trade(channel_name, nonce=nonce, rsmc=rsmc_trade, htlc=htlc_trade)

            if HtlcMessage.is_first_sender(router, sender):
                Channel.add_payment(channel_name, hashcode, None, payment)

        return None

    @classmethod
    def this_point(cls, sender, router=[]):
        for jumps in router:
            if sender in jumps:
                return router.index(jumps)

        return None

    @classmethod
    def is_first_sender(cls, router, sender):
        return router and sender in router[0]


class HtlcResponsesMessage(Message):
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

    def __init__(self, message, wallet):
        super().__init__(message)

        self.sender_balance = self.message_body.get('SenderBalance')
        self.receiver_balance = self.message_body.get('ReceiverBalance')
        self.commitment = self.message_body.get('Commitment')
        self.payment = self.message_body.get('Payment')
        self.delay_block = self.message_body.get('DelayBlock')
        self.delay_commitment = self.message_body.get('DelayCommitment')
        self.hashcode = self.message_body.get('HashR')

        self.router = message.get('Router', [])
        self.next_router = message.get('Next', None)

        self.wallet = wallet

    def check_if_the_last_router(self):
        return self.wallet.url == self.router[-1][0]

    def handle_message(self):
        self.handle()

    def handle(self):
        super(HtlcResponsesMessage, self).handle()

        verified, error = self.verify()
        if not verified:
            LOG.error(error)
            return

    @staticmethod
    def create(channel_name, wallet, sender, receiver, asset_type, payment, tx_nonce,
               hashcode, delay_block, rsmc_commitment, htlc_commitment, router, next_router, comments=None):
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
        :param rsmc_commitment:
        :param htlc_commitment:
        :param router:
        :param next_router:
        :param comments:
        :return:
        """
        message = HtlcMessage.create_message_header(receiver, sender, HtlcResponsesMessage._message_name,
                                                    channel_name, asset_type, tx_nonce)
        message = message.message_header
        message.update({'Router': router, 'Next': next_router,})
        message_body = {'HashR': hashcode}
        status = EnumResponseStatus.RESPONSE_OK
        nonce = tx_nonce
        conclusive_commitment = None
        inconclusive_commitment = None
        receiver_balance = 0
        sender_balance = 0

        try:
            channel = Channel(channel_name)

            # get nonce from latest trade
            latest_trade = channel.latest_trade(channel_name)
            if not latest_trade:
                status = EnumResponseStatus.RESPONSE_TRADE_MISSING_IN_DB
                raise GoTo('No trade records in this channel<{}> for HashR<{}>'.format(channel_name, hashcode))
            nonce = int(latest_trade.nonce)+1
            message.update({'TxNonce': nonce})

            sender_address, _, _ = uri_parser(sender)
            receiver_address, _, _ = uri_parser(receiver)
            asset_type = asset_type.upper()

            balance = channel.balance
            console_log.info(balance)
            sender_balance = HtlcResponsesMessage.float_calculate(
                balance.get(sender_address, {}).get(asset_type, 0), payment, False)
            if 0 > sender_balance:
                status = EnumResponseStatus.RESPONSE_TRADE_NOT_ENOUGH_BALANCE
                raise GoTo('Sender balance<{}> is not enough.'.format(sender_balance+float(payment)))

            sender_locked_balance = float(payment)
            receiver_balance = float(balance.get(receiver_address, {}).get(asset_type, 0))

            # 2 parts in htlc message: conclusive and inconclusive part
            # ToDo:
            conclusive_commitment = contract_event_api.sign_content(
                typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
                valueList=[channel_name, nonce, sender_address, sender_balance, receiver_address, receiver_balance],
                privtKey = wallet._key.private_key_string)

            inconclusive_commitment = contract_event_api.sign_content(
                start=5,
                typeList=['bytes32', 'uint256', 'address', 'address', 'uint256', 'uint256', 'bytes32'],
                valueList=[channel_name, nonce, sender_address, receiver_address,
                           delay_block, sender_locked_balance, hashcode],
                privtKey = wallet._key.private_key_string)

            message_body = {
                'SenderBalance': sender_balance,
                'ReceiverBalance': receiver_balance,
                'Commitment': conclusive_commitment,
                'Payment': payment,
                'DelayBlock': delay_block,
                'DelayCommitment': inconclusive_commitment,
                'HashR': hashcode
            }

            # record the payment
            channel.add_payment(channel_name, hashcode=hashcode, payment=payment, state=EnumTradeState.confirming)
        except GoTo as error:
            LOG.error(error)
        except Exception as error:
            status = EnumResponseStatus.RESPONSE_EXCEPTION_HAPPENED
            LOG.exception(error)
        finally:
            # whatever happened, we need record the trade
            # # add trade to database
            # # ToDo: need re-sign all unconfirmed htlc message later
            rsmc_trade = Channel.founder_or_rsmc_trade(
                role=EnumTradeRole.TRADE_ROLE_PARTNER, asset_type=asset_type, payment=0,
                balance=receiver_balance, peer_balance=sender_balance,
                commitment=conclusive_commitment, peer_commitment=rsmc_commitment, state=EnumTradeState.confirming
            )
            htlc_trade = Channel.htlc_trade(
                role=EnumTradeRole.TRADE_ROLE_PARTNER, asset_type=asset_type,
                hashcode=hashcode, rcode=None, payment=payment, delay_block=delay_block,
                commitment=inconclusive_commitment, peer_commitment=htlc_commitment, state=EnumTradeState.confirming)

            Channel.add_trade(channel_name, nonce=nonce, rsmc=rsmc_trade, htlc=htlc_trade)

            # orgnize the message
            message.update({'MessageBody': message_body})
            message.update({'Status': status.name})
            if comments:
                message.update({'Comments': comments})

            Message.send(message)

    def verify(self):
        verified, error = super(HtlcResponsesMessage, self).verify()
        if not verified:
            return verified, None

        if self.status not in [EnumResponseStatus.RESPONSE_OK.name, EnumResponseStatus.RESPONSE_OK.value]:
            return False, 'Response status error: <{}>'.format(self.status)

        return True, None
