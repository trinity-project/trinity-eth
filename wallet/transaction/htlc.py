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
from model.statistics_model import APIStatistics


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
        self.payment = int(self.message_body.get('PaymentCount', -1))

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
        payment = htlc_trade.payment

        message = RResponse.create_message_header(sender, receiver, RResponse._message_name,
                                                  channel_name, asset_type, nonce)

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
            stored_payment = int(htlc_trade.payment)
            if stored_payment != self.payment:
                raise GoTo(EnumResponseStatus.RESPONSE_TRADE_UNMATCHED_PAYMENT,
                           'Unmatched payment. self stored payment<{}>, peer payment<{}>'.format(stored_payment,
                                                                                                 self.payment))

            # send response OK message
            RResponseAck.create(self.channel_name, self.asset_type, self.nonce, self.sender, self.receiver,
                                self.hashcode, self.rcode, self.payment, self.comments, status)
        except TrinityException as error:
            LOG.error(error)
            status = error.reason
        except Exception as error:
            status = EnumResponseStatus.RESPONSE_EXCEPTION_HAPPENED
            LOG.error('Failed to handle RResponse with HashR<{}>. Exception: {}'.format(self.hashcode, error))
            pass
        else:
            # trigger rsmc
            self.trigger_pay_by_rsmc()

            # notify rcode to next peer
            LOG.debug('notify the RResponse to next channel<{}>, current channel<{}>'.format(htlc_trade.channel,
                                                                                             self.channel_name))
            self.notify_rcode_to_next_peer(htlc_trade.channel)
        finally:
            if EnumResponseStatus.RESPONSE_OK != status:
                RResponseAck.send_error_response(self.sender, self.receiver, self.channel_name, self.asset_type,
                                                 self.nonce, status)

        return None

    def trigger_pay_by_rsmc(self):
        try:
            # change htlc to rsmc
            RsmcMessage.create(self.channel_name, self.asset_type, self.wallet.url, self.sender,
                               self.payment, self.hashcode, comments=self.comments)
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

            htlc_trade = self.get_htlc_trade_by_hashr(next_channel, self.hashcode)
            if htlc_trade.role == EnumTradeRole.TRADE_ROLE_PARTNER.name and next_channel != htlc_trade.channel:
                LOG.warning('Why the channel is different. next_channel<{}>, stored channel<{}>' \
                          .format(next_channel, htlc_trade.channel))

            # notify the previous node the R-code
            LOG.debug('Payment get channel {}/{}'.format(next_channel, self.hashcode))
            channel = Channel(next_channel)
            channel.update_trade(next_channel, htlc_trade.nonce, rcode=self.rcode)
            peer = channel.peer_uri(self.wallet.url)
            nonce = channel.latest_nonce(next_channel)
            LOG.info("Next peer: {}".format(peer))
            self.create(next_channel, self.asset_type, nonce, self.wallet.url, peer,
                        self.hashcode, self.rcode, self.comments)

            APIStatistics.update_statistics(self.wallet.address, htlc_rcode=True)
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
    _sign_type_list = ['bytes32', 'address', 'address', 'uint256', 'uint256', 'bytes32']

    def __init__(self, message, wallet):
        super().__init__(message)

        self.sender_balance = self.message_body.get('SenderBalance')
        self.receiver_balance = self.message_body.get('ReceiverBalance')
        self.payment = self.message_body.get('Payment')
        self.commitment = self.message_body.get('Commitment')

        self.delay_block = self.message_body.get('DelayBlock')
        self.delay_commitment = self.message_body.get('DelayCommitment')
        self.hashcode = self.message_body.get('HashR')
        self.role_index = int(self.message_body.get('RoleIndex', -1))

        self.router = message.get('Router', [])
        self.wallet = wallet

    def check_if_the_last_router(self):
        return self.wallet.url in self.router[0] and len(self.router) in [0, 1]

    @classmethod
    def check_router(self, router, hashcode):
        if not router:
            raise GoTo(EnumResponseStatus.RESPONSE_ROUTER_VOID_ROUTER,
                       'Router<{}> NOT found for htlc trade with HashR<{}>'.format(router, hashcode))

        return True

    @classmethod
    def check_hashcode_used(cls, channel_name, hashcode):
        try:
            trade_record = Channel.batch_query_trade(channel_name, filters={'hashcode': hashcode})[0]
        except Exception as error:
            return True
        else:
            raise GoTo(EnumResponseStatus.RESPONSE_TRADE_HASHR_ALREADY_EXISTED,
                       'HashR<{}> already used by trade with nonce<{}>'.format(hashcode, trade_record.nonce))

    @classmethod
    def exclude_wallet_from_router(cls, current_url, router):
        """
        Description: remove current wallet url from the router
        :param router: router from messages
        :return:
        """
        try:
            router_url = [jump[0] for jump in router]
            this_jump = router_url.index(current_url)
        except Exception as error:
            raise GoTo(
                EnumResponseStatus.RESPONSE_ROUTER_WITHOUT_CURRENT_WALLET,
                'Why wallet<{}> receive this messages. Router<{}> without current wallet'
                    .format(current_url, router)
            )
        else:
            return router[this_jump+1:], router[this_jump]

    @property
    def next_jump(self):
        return self.router[0][0] if self.router and self.router[0] else None

    @classmethod
    def request(cls, sender_balance, receiver_balance, payment, hashcode, unlocked_block):
        """

        :param payment:
        :param sender_balance:
        :param receiver_balance:
        :param unlocked_block:
        :param hashcode:
        :return:
        """
        request_message_body = {
            'SenderBalance': str(sender_balance),
            'ReceiverBalance': str(receiver_balance),
            'Payment': str(payment),
            'HashR': hashcode
        }

        if unlocked_block:
            request_message_body.update({'DelayBlock': str(unlocked_block)})

        return request_message_body

    @classmethod
    def response(cls, sender_balance, receiver_balance, payment, hashcode, role_index=0, delay_block=None):
        """

        :param payment:
        :param sender_balance:
        :param receiver_balance:
        :param role_index:
        :param hashcode:
        :return:
        """
        response_message_body = cls.request(sender_balance, receiver_balance, payment, hashcode, delay_block)
        response_message_body.update({'RoleIndex': role_index})
        return response_message_body

    def get_fee(self, url):
        router_url = [i[0] for i in self.router]
        index = router_url.index(url)
        try:
            return self.router[index][1]
        except IndexError:
            return 0


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

    def __init__(self, message, wallet=None):
        super(HtlcMessage, self).__init__(message, wallet)
        self.htlc_sign_role = 0
        self.role_index = -1
        self.get_payer_and_payee_address()

    def handle_message(self):
        self.handle()

    def handle(self):
        super(HtlcMessage, self).handle()

        trigger_rresponse = False
        status = EnumResponseStatus.RESPONSE_OK
        resign_ack = None
        resign_request = None
        nonce = None
        try:
            # common check
            self.check_channel_state(self.channel_name)
            self.check_router(self.router, self.hashcode)
            self.verify()

            # resign request by peer ??
            if self.resign_body:
                resign_ack, nego_trade = self.handle_resign_body(self.wallet, self.channel_name, self.resign_body)
            else:
                # check whether need resign previous transaction
                resign_request, nego_trade = self.create_resign_message_body(self.channel_name, self.nonce)

            # real nonce
            nego_nonce = nego_trade and (nego_trade.nonce+1)
            nonce = nego_nonce or self.nonce

            # some local variables to save later
            htlc_sign_body = self.response(self.sender_balance, self.receiver_balance, self.payment, self.hashcode,
                                           self.htlc_sign_role, self.delay_block)
            htlc_trade = Channel.htlc_trade(
                type=EnumTradeType.TRADE_TYPE_HTLC, role=EnumTradeRole.TRADE_ROLE_PARTNER, asset_type=self.asset_type,
                balance=self.receiver_balance, peer_balance=self.sender_balance, payment=self.payment,
                hashcode=self.hashcode, delay_block=self.delay_block, channel=self.channel_name)

            # if need resign, just send resign message body
            sign_hashcode, sign_rcode = self.get_default_rcode()
            if resign_request:
                # add resign body to response body
                htlc_sign_body.update({'ResignBody': resign_request})
            else:
                # check the balance
                _, payer_balance, payee_balance = self.check_balance(
                self.channel_name, self.asset_type, self.payer_address, self.sender_balance,
                self.payee_address, self.receiver_balance, is_htcl_type=True, payment=self.payment)

                # sign the transaction
                # 2 parts in htlc message: conclusive and inconclusive part
                rsmc_commitment = HtlcMessage.sign_content(
                    self.wallet, RsmcMessage._sign_type_list,
                    [self.channel_name, nonce, self.payer_address, payer_balance, self.payee_address, payee_balance,
                     sign_hashcode, sign_rcode]
                )

                hlock_commitment = HtlcMessage.sign_content(
                    self.wallet, self._sign_type_list,
                    [self.channel_name, self.payer_address, self.payee_address, int(self.delay_block),
                     int(self.payment), self.hashcode],
                    start=5
                )

                # update the htlc_trade
                htlc_trade.update({'commitment':rsmc_commitment,
                                   'delay_commitment': hlock_commitment,
                                   'state': EnumTradeState.confirming.name
                                   })

                # update the message body with signature
                htlc_sign_body.update({'Commitment': rsmc_commitment, 'DelayCommitment': hlock_commitment})

                # add resign ack
                if resign_ack:
                    htlc_sign_body.update({'ResignBody': resign_ack})

            # Response message header
            response_message = HtlcResponsesMessage.create_message_header(
                self.receiver, self.sender, HtlcResponsesMessage._message_name, self.channel_name, self.asset_type,
                self.nonce, nego_nonce
            )
            response_message.update({'MessageBody': htlc_sign_body})
            response_message.update({'Status': status.name})
            self.send(response_message)

            # record the transaction
            if nonce != self.nonce:
                Channel.update_trade(self.channel_name, nonce=nonce, **htlc_trade)
            else:
                Channel.add_trade(self.channel_name, nonce=nonce, **htlc_trade)
        except TrinityException as error:
            LOG.exception(error)
            status = error.reason
        except Exception as error:
            LOG.exception('Failed to handle Htlc message for channel<{}>, HashR<{}>. Exception:{}'
                          .format(self.channel_name, self.hashcode, error))
            status = EnumResponseStatus.RESPONSE_EXCEPTION_HAPPENED
        finally:
            # failed operation
            if EnumResponseStatus.RESPONSE_OK != status:
                # send error response
                HtlcResponsesMessage.send_error_response(self.sender, self.receiver, self.channel_name,
                                                         self.asset_type, self.nonce, status)

                # delete some related resources
                self.rollback_resource(self.channel_name, nonce or self.nonce, self.payment, status.name)

        return

    @classmethod
    def get_unlocked_block_height(cls, total_routers):
        """

        :param total_routers:
        :return:
        """
        if not isinstance(total_routers, int):
            return 0

        unlocked_block_height = get_block_count() + HtlcMessage._block_per_day*total_routers

        return unlocked_block_height

    @classmethod
    def create(cls, channel_name, asset_type, sender, receiver, payment, hashcode, router, current_channel=None,
               comments=None):
        """

        :param channel_name:
        :param asset_type:
        :param sender:
        :param receiver:
        :param payment:
        :param hashcode:
        :param router:
        :param current_channel:
        :param comments:
        :return:
        """
        cls.check_channel_state(channel_name)
        cls.check_router(router, hashcode)
        cls.check_asset_type(asset_type)
        cls.check_both_urls(sender, receiver)

        payer_address, _, _ = uri_parser(sender)
        payee_address, _, _ = uri_parser(receiver)
        asset_type = asset_type.upper()
        channel = Channel(channel_name)

        # get nonce
        nonce = Channel.new_nonce(channel_name)
        if HtlcMessage._FOUNDER_NONCE > nonce:
            raise GoTo(EnumResponseStatus.RESPONSE_TRADE_WITH_INCORRECT_NONCE,
                       'HtlcMessage::create: Incorrect nonce<{}> for channel<{}>'.format(nonce, channel_name))

        # to check whether previous transaction need be resigned or not
        resign_body, valid_trade = HtlcMessage.create_resign_message_body(channel_name, nonce)

        # there're one trade need resign, we need adjust the nonce value
        if valid_trade and valid_trade.state in [EnumTradeState.confirming.name]:
            nonce = valid_trade.nonce + 1
            if EnumTradeRole.TRADE_ROLE_PARTNER.name == valid_trade.role:
                payer_balance = valid_trade.peer_balance
                payee_balance = valid_trade.balance
            else:
                payer_balance = valid_trade.balance
                payee_balance = valid_trade.peer_balance
        else:
            # to get channel balance
            balance = channel.balance
            payer_balance = balance.get(payer_address).get(asset_type)
            payee_balance = balance.get(payee_address).get(asset_type)

        # To calculate the balance after payment
        _, payer_balance, payee_balance = HtlcMessage.calculate_balance_after_payment(
            payer_balance, payee_balance, payment, is_htlc_type=True
        )

        # exclude current router from the router
        router, _ = HtlcMessage.exclude_wallet_from_router(sender, router)
        end_block_height = cls.get_unlocked_block_height(len(router))

        # generate htlc transaction and record it into database later
        htlc_trade = Channel.htlc_trade(
            type=EnumTradeType.TRADE_TYPE_HTLC, role=EnumTradeRole.TRADE_ROLE_FOUNDER, asset_type=asset_type,
            balance=payer_balance, peer_balance=payee_balance, payment=payment, hashcode=hashcode,
            delay_block=end_block_height
        )

        # record the channel if RResponse is triggered
        if current_channel:
            htlc_trade.update({'channel': current_channel})

        # create message
        htlc_request = HtlcMessage.request(payer_balance, payee_balance, payment, hashcode, end_block_height)
        # has transaction which is needed to be resigned
        if resign_body:
            htlc_request.update({'ResignBody': resign_body})

        # start to create message  and send later
        message = HtlcMessage.create_message_header(sender, receiver, HtlcMessage._message_name,
                                                    channel_name, asset_type, nonce)
        message.update({'Router': router})
        message.update({'MessageBody': htlc_request})

        if comments:
            message.update({'Comments': comments})

        HtlcMessage.send(message)

        # record the transaction
        Channel.add_trade(channel_name, nonce=nonce, **htlc_trade)

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

    def __init__(self, message, wallet):
        super(HtlcResponsesMessage, self).__init__(message, wallet)
        self.rsmc_sign_role = 1
        self.get_payer_and_payee_address()

    def handle_message(self):
        self.handle()

    def handle(self):
        super(HtlcResponsesMessage, self).handle()

        status = EnumResponseStatus.RESPONSE_OK
        try:
            # check the response status
            if not self.check_response_status(self.status):
                self.rollback_resource(self.channel_name, self.nonce, self.payment, status=self.status)
                return

            self.check_channel_state(self.channel_name)
            self.check_router(self.router, self.hashcode)
            self.verify()
            # _, nonce = self.check_nonce(self.nonce + 1, self.channel_name)
            # _, payer_balance, payee_balance = self.check_balance(
            #     self.channel_name, self.asset_type, self.receiver_address, self.sender_balance,
            #     self.sender_address, self.receiver_balance, is_htcl_type=True, payment=self.payment)

            # To handle the founder and partner response by role index
            if 0 == self.role_index:
                need_update_balance, htlc_sign_body = self.handle_partner_response()
            elif 1 == self.role_index:
                need_update_balance, htlc_sign_body = self.handle_founder_response()
            else:
                raise GoTo(EnumResponseStatus.RESPONSE_TRADE_INCORRECT_ROLE,
                           'Invalid Role<{}> of HtlcResponse'.format(self.role_index))

            # send HtlcSign to peer
            if htlc_sign_body:
                response_message = self.create_message_header(
                    self.receiver, self.sender, self._message_name, self.channel_name,
                    self.asset_type, self.nego_nonce or self.nonce
                )
                response_message.update({'Router': self.router})
                response_message.update({'MessageBody': htlc_sign_body})
                response_message.update({'Status': status.name})
                self.send(response_message)

            # update the channel balance
            if need_update_balance:
                self.update_balance_for_channel(self.channel_name, self.asset_type, self.payer_address,
                                                self.payee_address, self.payment, is_htlc_type=True)

                # now we need trigger htlc to next jump

        except TrinityException as error:
            LOG.exception(error)
            status = error.reason
        except Exception as error:
            LOG.exception('Transaction with none<{}> not found. Error: {}'.format(self.nonce, error))
            status = EnumResponseStatus.RESPONSE_EXCEPTION_HAPPENED
        else:
            # successful action
            LOG.debug('Succeed to htlc for channel<{}>'.format(self.channel_name))
            return
        finally:
            # rollback the resources
            self.rollback_resource(self.channel_name, self.nonce, self.payment, status=status.name)

    def handle_partner_response(self):
        """

        :return: response to send to peer
        """
        # local variables
        need_update_balance = False

        # handle the resign body firstly
        resign_ack = None
        resign_trade = None
        if self.resign_body:
            resign_ack, resign_trade = self.handle_resign_body(self.wallet, self.channel_name, self.resign_body)

            # here if the peer not provide the signature, we need re-calculate the balance based on resign trade
            if not (self.commitment and self.delay_commitment):
                _, self.sender_balance, self.receiver_balance = self.calculate_balance_after_payment(
                    resign_trade.balance, resign_trade.peer_balance, self.payment, is_htlc_type=True
                )

        # if transaction partner provide the negotiated nonce
        if self.nego_nonce:
            self.validate_negotiated_nonce()

        htlc_sign_body = self.response(self.sender_balance, self.receiver_balance, self.payment, self.hashcode, 1,
                                       self.delay_block)

        # get some common local variables
        sign_hashcode, sign_rcode = self.get_default_rcode()
        payer_balance = int(self.sender_balance)
        payee_balance = int(self.receiver_balance)
        payment = int(self.payment)
        commitment = None
        delay_commitment = None

        # use this nonce for following message of current transaction
        nonce = self.nego_nonce or self.nonce

        # start to sign this new transaction and save it
        try:
            old_trade = Channel.query_trade(self.channel_name, self.nonce)
            payment = int(old_trade.payment)

            if self.nonce == nonce:
                commitment = old_trade.commitment
                delay_commitment = old_trade.delay_commitment
        except:
            pass
        finally:
            if not (commitment and delay_commitment):
                # check balance
                self.check_balance(self.channel_name, self.asset_type, self.payer_address, payer_balance,
                                   self.payee_address, payee_balance, is_htcl_type=True, payment=payment)

                # sign the transaction with 2 parts: rsmc and htlc-locked part
                commitment = self.sign_content(
                    self.wallet, RsmcMessage._sign_type_list,
                    [self.channel_name, nonce, self.payer_address, payer_balance,
                     self.payee_address, payee_balance, sign_hashcode, sign_rcode]
                )

                delay_commitment = self.sign_content(
                    self.wallet, self._sign_type_list,
                    [self.channel_name, self.payer_address, self.payee_address, self.delay_block,
                     int(payment), self.hashcode],
                    start=5
                )

                # generate the htlc trade
                htlc_trade = Channel.htlc_trade(
                    type=EnumTradeType.TRADE_TYPE_HTLC, role=EnumTradeRole.TRADE_ROLE_PARTNER, asset_type=self.asset_type,
                    balance=payer_balance, peer_balance=payee_balance, payment=payment, hashcode=self.hashcode,
                    delay_block=self.delay_block, commitment=commitment, delay_commitment=delay_commitment)

                Channel.update_trade(self.channel_name, nonce, **htlc_trade)

        # delete the transaction with self.nonce ????
        if nonce != self.nonce:
            Channel.delete_trade(self.channel_name, self.nonce)

        # peer has already sign the new transaction with nonce
        if self.commitment and self.delay_commitment:
            # check the signature of rsmc part
            self.check_signature(
                self.wallet, self.sender_address,
                type_list=RsmcMessage._sign_type_list,
                value_list=[self.channel_name, nonce, self.payer_address, int(self.sender_balance),
                            self.payee_address, int(self.receiver_balance), sign_hashcode, sign_rcode],
                signature=self.commitment
            )

            # check signature of htlc-lock part
            self.check_signature(
                self.wallet, self.sender_address,
                type_list=self._sign_type_list,
                value_list=[self.channel_name, self.payer_address, self.payee_address, self.delay_block,
                            int(payment), self.hashcode],
                signature=self.delay_commitment
            )

            # update this trade confirmed state
            Channel.update_trade(self.channel_name, nonce, commitment=commitment, delay_commitment=delay_commitment,
                                 peer_commitment=self.commitment, peer_delay_commitment=self.delay_commitment,
                                 state=EnumTradeState.confirmed.name)
            need_update_balance = True

            htlc_sign_body.update({'Commitment': commitment, 'DelayCommitment': delay_commitment})

        # has resign response ??
        if resign_ack:
            htlc_sign_body.update({'ResignBody': resign_ack})

        return need_update_balance, htlc_sign_body

    def handle_founder_response(self):
        """

        :return:
        """
        need_update_balance = False
        # handle the resign body firstly
        resign_ack = None
        if self.resign_body:
            resign_ack, _ = self.handle_resign_body(self.wallet, self.channel_name, self.resign_body)

        sign_hashcode, sign_rcode = self.get_default_rcode()
        # has already signed by peer
        if self.commitment and self.delay_commitment:
            # check the signature
            self.check_signature(
                self.wallet, self.sender_address,
                type_list=RsmcMessage._sign_type_list,
                value_list=[self.channel_name, self.nonce, self.payer_address, int(self.sender_balance),
                            self.payee_address, int(self.receiver_balance), sign_hashcode, sign_rcode],
                signature=self.commitment
            )

            # check signature of htlc-lock part
            self.check_signature(
                self.wallet, self.sender_address,
                type_list=self._sign_type_list,
                value_list=[self.channel_name, self.payer_address, self.payee_address, self.delay_block,
                            int(self.payment), self.hashcode],
                signature=self.delay_commitment
            )
            # Just update current transaction confirmed:
            Channel.update_trade(self.channel_name, self.nonce, peer_commitment=self.commitment,
                                 state=EnumTradeState.confirmed.name)

            # trigger htlc or RResponse
            self.trigger_htlc_to_next_jump()
            need_update_balance = True
        else:
            # to check the latest confirmed nonce
            confirmed_nonce = Channel.latest_confirmed_nonce(self.channel_name)
            if confirmed_nonce != self.nonce - 1:
                raise GoTo(
                    EnumResponseStatus.RESPONSE_TRADE_RESIGN_REQUEST_NOT_IMPLEMENTED,
                    'Wait for next resign. current confirmed nonce<{}>, request nonce<{}>'.format(confirmed_nonce,
                                                                                                  self.nonce)
                )

            # check balance after resign successfully
            self.check_balance(self.channel_name, self.asset_type, self.payer_address, self.sender_balance,
                               self.payee_address, self.receiver_balance, is_htcl_type=True, payment=self.payment)

            # sign this transaction
            # sign the transaction with 2 parts: rsmc and htlc-locked part
            commitment = self.sign_content(
                self.wallet, RsmcMessage._sign_type_list,
                [self.channel_name, self.nonce, self.payer_address, self.sender_balance,
                 self.payee_address, self.receiver_balance, sign_hashcode, sign_rcode]
            )

            delay_commitment = self.sign_content(
                self.wallet, self._sign_type_list,
                [self.channel_name, self.payer_address, self.payee_address, self.delay_block,
                 int(self.payment), self.hashcode],
                start=5
            )

            # update the transaction confirming state
            Channel.update_trade(
                self.channel_name, self.nonce, balance=self.receiver_balance, peer_balance=self.sender_balance,
                commitment=commitment, delay_commitment=delay_commitment, state=EnumTradeState.confirming.name
            )

            # re-trigger the new transaction saved in db before
            htlc_sign_body = self.response(self.sender_balance, self.receiver_balance, self.payment, self.hashcode, 0,
                                           self.delay_block)
            htlc_sign_body.update({'Commitment': commitment, 'DelayCommitment': delay_commitment})

            return need_update_balance, htlc_sign_body

        return need_update_balance, None

    def trigger_htlc_to_next_jump(self):
        """"""
        if not self.check_if_the_last_router():
            next_router = self.next_jump
            LOG.debug('Get Next Router {}'.format(str(next_router)))

            if not next_router:
                raise GoTo(
                    EnumResponseStatus.RESPONSE_ROUTER_WITH_ILLEGAL_NEXT_JUMP,
                    'Illegal next jump<{}> in router<{}>'.format(next_router, self.router)
                )

            # to get channel between current wallet and next jump
            channel_set = Channel.get_channel(self.wallet.url, next_router, state=EnumChannelState.OPENED)
            if not (channel_set and channel_set[0]):
                raise GoTo(EnumResponseStatus.RESPONSE_CHANNEL_NOT_FOUND,
                           'No OPENED channel is found between {} and {}.'.format(self.wallet.url, next_router))
            channel_set = channel_set[0]

            # calculate fee and transfer to next jump
            fee = TrinityNumber(str(self.get_fee(self.wallet.url))).number
            payment = self.big_number_calculate(self.payment, fee, False)
            receiver = next_router
            HtlcMessage.create(channel_set.channel, self.asset_type, self.wallet.url, receiver, payment, self.hashcode,
                               self.router, current_channel=self.channel_name, comments=self.comments)

            # record channel of next jump in current htlc trade
            Channel.update_trade(self.channel_name, self.nonce, channel=channel_set.channel)

            APIStatistics.update_statistics(self.wallet.address, htlc_free=fee)
        else:
            # trigger RResponse
            Channel.update_payment(self.channel_name, self.hashcode)
            payment_trade = Channel.query_payment(self.channel_name, self.hashcode)
            if not (payment_trade and payment_trade[0]):
                raise GoTo(
                    EnumResponseStatus.RESPONSE_TRADE_HASHR_NOT_FOUND,
                    'Rcode not found for hashcode<{}>'.format(self.hashcode)
                )

            payment_trade = payment_trade[0]

            try:
                RResponse.create(self.channel_name, self.asset_type, self.nonce, self.wallet.url, self.sender,
                                 self.hashcode, payment_trade.rcode, self.comments)

                # update the htlc trade history
                Channel.update_trade(self.channel_name, self.nonce, rcode=payment_trade.rcode)
            except Exception as error:
                LOG.exception('Failed triggerring to send RResponse for HashR<{}>. Exception: {}'
                              .format(self.hashcode, error))
