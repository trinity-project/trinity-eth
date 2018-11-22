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
from .payment import PaymentAck

from common.log import LOG
from common.common import uri_parser
from common.number import TrinityNumber
from common.exceptions import GoTo, TrinityException
from wallet.channel import Channel
from wallet.channel import EnumTradeType, EnumTradeRole, EnumTradeState
from model.statistics_model import APIStatistics


class RsmcBase(TransactionBase):
    """
    Description:
    """
    _sign_type_list = ['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256', 'bytes32', 'bytes32']

    def __init__(self, message, wallet=None):
        super(RsmcBase, self).__init__(message)

        self.payment = self.message_body.get('PaymentCount')
        self.sender_balance = self.message_body.get('SenderBalance')
        self.receiver_balance = self.message_body.get('ReceiverBalance')
        self.commitment = self.message_body.get('Commitment')
        self.role_index = int(self.message_body.get('RoleIndex', -1))
        self.hashcode = self.message_body.get('HashR')
        self.wallet = wallet

    @classmethod
    def check_role(cls, role):
        # row index related check
        if int(role) not in [0, 1]:
            raise GoTo(EnumResponseStatus.RESPONSE_TRADE_INCORRECT_ROLE,
                       'RsmcSign with illegal role index<{}>'.format(role))

        return True

    @classmethod
    def request(cls, asset_type, payment, sender_balance, receiver_balance, hashcode=None):
        """

        :param asset_type:
        :param payment:
        :param sender_balance:
        :param receiver_balance:
        :param hashcode:
        :return:
        """
        request_message_body = {
            'AssetType': asset_type,
            'PaymentCount': str(payment),
            'SenderBalance': str(sender_balance),
            'ReceiverBalance': str(receiver_balance),
        }

        if hashcode:
            request_message_body.update({'HashR': hashcode})

        return request_message_body

    @classmethod
    def response(cls, asset_type, payment, sender_balance, receiver_balance, role_index=0, hashcode=None):
        """

        :param asset_type:
        :param payment:
        :param sender_balance:
        :param receiver_balance:
        :param role_index:
        :param hashcode:
        :return:
        """
        response_message_body = cls.request(asset_type, payment, sender_balance, receiver_balance, hashcode)
        response_message_body.update({'RoleIndex': role_index})
        return response_message_body

    def notify_peer_payment_finished(self,):
        try:
            payment_record = Channel.query_payment(self.channel_name, self.comments)[0]
            receiver = payment_record.receiver
        except:
            LOG.warning('No payment record with code<{}> is found'.format(self.comments))
            pass
        else:
            PaymentAck.create(self.wallet.url, receiver, self.channel_name, self.asset_type, self.nonce,
                              self.comments)

        return

class RsmcMessage(RsmcBase):
    """
    {
        'MessageType':'Rsmc',
        'Sender': sender,
        'Receiver': receiver,
        'TxNonce': nonce,
        'ChannelName':channel_name,
        'NetMagic': RsmcMessage.get_magic(),
        'AssetType':asset_type.upper(),
        'MessageBody': {
            'PaymentCount': payment,
            'SenderBalance': sender_balance,
            'ReceiverBalance': receiver_balance,
            'HashR': hasr, default: '0x'+'0'*32
        }
        'Comments': {}
    }
    """
    _message_name = 'Rsmc'

    def __init__(self, message, wallet=None):
        super(RsmcMessage, self).__init__(message, wallet)
        self.rsmc_sign_role = 0
        self.role_index = -1
        self.get_payer_and_payee_address()

    def handle_message(self):
        self.handle()

    def handle(self):
        super(RsmcMessage, self).handle()

        status = EnumResponseStatus.RESPONSE_OK
        resign_ack = None
        resign_request = None
        try:
            # common check
            self.check_channel_state(self.channel_name)
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

            rsmc_sign_body = self.response(self.asset_type, self.payment, self.sender_balance, self.receiver_balance,
                                           self.rsmc_sign_role, self.hashcode)

            # record the transaction without any signature
            sign_hashcode, sign_rcode = self.get_rcode(self.channel_name, self.hashcode)
            rsmc_trade = Channel.rsmc_trade(
                type=EnumTradeType.TRADE_TYPE_RSMC, role=EnumTradeRole.TRADE_ROLE_PARTNER, asset_type=self.asset_type,
                balance=self.receiver_balance, peer_balance=self.sender_balance, payment=self.payment,
                hashcode=sign_hashcode, rcode=sign_rcode
            )

            # if need resign, just send resign message body
            if resign_request:
                # add resign body to message body
                rsmc_sign_body.update({'ResignBody': resign_request})
            else:
                # check the balance
                htlc_to_rsmc = self.is_hlock_to_rsmc(self.hashcode)
                _, payer_balance, payee_balance = self.check_balance(
                    self.channel_name, self.asset_type, self.payer_address, self.sender_balance,
                    self.payee_address, self.receiver_balance, hlock_to_rsmc=htlc_to_rsmc, payment=self.payment
                )

                # sign the trade
                commitment = RsmcResponsesMessage.sign_content(
                    self.wallet, RsmcMessage._sign_type_list, [self.channel_name, nonce, self.payer_address,
                                                               payer_balance, self.payee_address, payee_balance,
                                                               sign_hashcode, sign_rcode]
                )

                # update the rsmc_trade
                rsmc_trade.update({'commitment': commitment, 'state':EnumTradeState.confirming.name})

                # update the message body with signature
                rsmc_sign_body.update({'Commitment': commitment})

                # add resign ack
                if resign_ack:
                    rsmc_sign_body.update({'ResignBody': resign_ack})

            # Response message header
            response_message = RsmcResponsesMessage.create_message_header(
                self.receiver, self.sender, RsmcResponsesMessage._message_name, self.channel_name, self.asset_type,
                self.nonce, nego_nonce
            )
            response_message.update({'MessageBody': rsmc_sign_body})
            response_message.update({'Status': status.name})
            self.send(response_message)

            # record the transaction
            self.record_transaction(nonce, **rsmc_trade)
            APIStatistics.update_statistics(self.wallet.address, rsmc='rsmc')
        except TrinityException as error:
            status = error.reason
            LOG.exception(error)
        except Exception as error:
            status = EnumResponseStatus.RESPONSE_EXCEPTION_HAPPENED
            LOG.exception('Failed to handle RsmcMessage. Exception: {}'.format(error))
        finally:
            if EnumResponseStatus.RESPONSE_OK != status:
                # nofify error response
                RsmcResponsesMessage.send_error_response(self.sender, self.receiver, self.channel_name, self.asset_type,
                                                         self.nonce, status)

        return

    @staticmethod
    def create(channel_name, asset_type, sender, receiver, payment, hashcode=None, comments=None):
        """

        :param channel_name:
        :param asset_type:
        :param sender:
        :param receiver:
        :param payment:
        :param hashcode:
        :param comments:
        :param hlock_to_rsmc:
        :return:
        """
        # check channel state
        RsmcMessage.check_asset_type(asset_type)
        channel = RsmcMessage.check_channel_state(channel_name)
        payer_address, _, _ = uri_parser(sender)
        payee_address, _, _ = uri_parser(receiver)
        asset_type = asset_type.upper()
        resign_body = None

        # get nonce in the offline account book
        nonce = Channel.new_nonce(channel_name)
        if RsmcMessage._FOUNDER_NONCE > nonce:
            raise GoTo(EnumResponseStatus.RESPONSE_TRADE_WITH_INCORRECT_NONCE,
                       'RsmcMessage::create: Incorrect nonce<{}> for channel<{}>'.format(nonce, channel_name))

        # to check whether there's a transaction which is needed to resign
        resign_body, valid_trade = RsmcMessage.create_resign_message_body(channel_name, nonce)

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

        # judge whether it is htlc lock part to rsmc trade or not
        hlock_to_rsmc = RsmcMessage.is_hlock_to_rsmc(hashcode)
        _, payer_balance, payee_balance = RsmcBase.calculate_balance_after_payment(
            payer_balance, payee_balance, payment, hlock_to_rsmc=hlock_to_rsmc
        )

        # sign the trade
        sign_hashcode, sign_rcode = RsmcMessage.get_rcode(channel_name, hashcode)
        rsmc_trade = Channel.rsmc_trade(
            type=EnumTradeType.TRADE_TYPE_RSMC, role=EnumTradeRole.TRADE_ROLE_FOUNDER, asset_type=asset_type,
            balance=payer_balance, peer_balance=payee_balance, payment=payment,
            hashcode=sign_hashcode, rcode=sign_rcode
        )

        # create message
        rsmc_request = RsmcMessage.request(asset_type, payment, payer_balance, payee_balance, hashcode)
        # has transaction which is needed to be resigned
        if resign_body:
            rsmc_request.update({'ResignBody': resign_body})

        # start to create message
        message = RsmcMessage.create_message_header(sender, receiver, RsmcMessage._message_name,
                                                    channel_name, asset_type, nonce)
        message.update({'MessageBody': rsmc_request})
        if comments:
            message.update({'Comments': comments})

        RsmcMessage.send(message)

        # record the transaction
        Channel.add_trade(channel_name, nonce=nonce, **rsmc_trade)
        APIStatistics.update_statistics(payer_address, rsmc='rsmc')

        return None


class RsmcResponsesMessage(RsmcBase):
    """
    message = {
        'MessageType':'RsmcSign',
        'Sender': receiver,
        'Receiver': sender,
        'TxNonce': nonce,
        'ChannelName':channel_name,
        'NetMagic': RsmcMessage.get_magic(),
        'MessageBody': {
            'AssetType':asset_type.upper(),
            'PaymentCount': payment,
            'SenderBalance': this_receiver_balance,
            'ReceiverBalance': this_sender_balance,
            'Commitment': commitment,
        }
        'Comments': {},
        'Status':
    }
    """
    _message_name = 'RsmcSign'

    def __init__(self, message, wallet):
        super(RsmcResponsesMessage, self).__init__(message, wallet)
        self.rsmc_sign_role = 1
        self.get_payer_and_payee_address()

    def handle_message(self):
        self.handle()

    def handle(self):
        super(RsmcResponsesMessage, self).handle()

        status = EnumResponseStatus.RESPONSE_OK
        try:
            # check the response status
            if not self.check_response_status(self.status):
                self.rollback_resource(self.channel_name, self.nonce, self.payment, self.status)
                return
            # common check
            self.check_channel_state(self.channel_name)
            self.verify()
            self.check_role(self.role_index)

            if 0 == self.role_index:
                need_update_balance, rsmc_sign_body = self.handle_partner_response()
            elif 1 == self.role_index:
                need_update_balance, rsmc_sign_body = self.handle_founder_response()
            else:
                raise GoTo(EnumResponseStatus.RESPONSE_FAIL, 'Invalid Role<{}> of RsmcResponse'.format(self.role_index))

            # send RsmcSign to peer
            if rsmc_sign_body:
                response_message = self.create_message_header(self.receiver, self.sender, self._message_name,
                                                              self.channel_name, self.asset_type, self.nego_nonce or self.nonce)
                response_message.update({'MessageBody': rsmc_sign_body})
                response_message.update({'Status': status.name})
                self.send(response_message)

            is_htlc_to_rsmc = self.is_hlock_to_rsmc(self.hashcode)
            if is_htlc_to_rsmc:
                # update the htlc transaction state.
                Channel.confirm_payment(self.channel_name, self.hashcode, is_htlc_to_rsmc)

            # update the channel balance
            if need_update_balance:
                APIStatistics.update_statistics(self.wallet.address, payment=self.payment, payer=(0==self.role_index))
                self.update_balance_for_channel(self.channel_name, self.asset_type, self.payer_address,
                                                self.payee_address, self.payment, is_htlc_to_rsmc)
        except GoTo as error:
            LOG.exception(error)
            status = error.reason
        except Exception as error:
            status = EnumResponseStatus.RESPONSE_EXCEPTION_HAPPENED
            LOG.exception('Failed to handle RsmcSign for channel<{}> nonce<{}>, role_index<{}>.Exception: {}' \
                      .format(self.channel_name, self.nonce, self.role_index, error))
        finally:
            # send error response
            if EnumResponseStatus.RESPONSE_OK != status:
                if 0 == self.role_index:
                    self.send_error_response(self.sender, self.receiver, self.channel_name,
                                             self.asset_type, self.nonce, status, kwargs={'RoleIndex': '1'})

                # need rollback some resources
                self.rollback_resource(self.channel_name, self.nonce, self.payment, status=self.status)

        return

    def handle_partner_response(self):
        """

        :return: response to send to peer
        """
        # local variables
        need_update_balance = False
        is_htlc_to_rsmc = self.is_hlock_to_rsmc(self.hashcode)

        # handle the resign body firstly
        resign_ack = None
        resign_trade = None
        if self.resign_body:
            resign_ack, resign_trade = self.handle_resign_body(self.wallet, self.channel_name, self.resign_body)

            # here if the peer not provide the signature, we need re-calculate the balance
            if not self.commitment:
                _, self.sender_balance, self.receiver_balance = self.calculate_balance_after_payment(
                    resign_trade.balance, resign_trade.peer_balance, self.payment, is_htlc_to_rsmc
                )

        # check the trade state by the nego_nonce if provided by peer
        if self.nego_nonce:
            # to check whether the negotiated nonce is legal or not
            self.validate_negotiated_nonce()

        rsmc_sign_body = self.response(self.asset_type, self.payment, self.sender_balance, self.receiver_balance,
                                       1, self.hashcode)

        # get some common local variables
        sign_hashcode, sign_rcode = self.get_rcode(self.channel_name, self.hashcode)
        payer_balance = int(self.sender_balance)
        payee_balance = int(self.receiver_balance)
        payment = int(self.payment)
        commitment = None

        # use this nonce for following message of current transaction
        nonce = self.nego_nonce or self.nonce

        # start to sign this new transaction and save it
        try:
            old_trade = Channel.query_trade(self.channel_name, self.nonce)
            payment = int(old_trade.payment)

            if self.nonce == nonce:
                commitment = old_trade.commitment
        except:
            pass
        finally:
            if not commitment:
                # check balance
                self.check_balance(self.channel_name, self.asset_type, self.payer_address, payer_balance,
                                   self.payee_address, payee_balance, hlock_to_rsmc=is_htlc_to_rsmc, payment=payment)

                # sign the transaction
                commitment = RsmcResponsesMessage.sign_content(
                    self.wallet, self._sign_type_list, [self.channel_name, nonce, self.payer_address, payer_balance,
                                                        self.payee_address, payee_balance, sign_hashcode, sign_rcode]
                )

                # generate the rsmc trade part
                rsmc_trade = Channel.rsmc_trade(
                    type=EnumTradeType.TRADE_TYPE_RSMC, role=EnumTradeRole.TRADE_ROLE_FOUNDER,
                    asset_type=self.asset_type, balance=payer_balance, peer_balance=payee_balance, payment=payment,
                    hashcode=sign_hashcode, rcode=sign_rcode, commitment=commitment
                )

                Channel.update_trade(self.channel_name, nonce, **rsmc_trade)

        # if negotiated nonce by peer, delete the transaction with self.nonce ????
        if nonce != self.nonce:
            Channel.delete_trade(self.channel_name, self.nonce)

        # peer has already sign the new transaction with nonce
        if self.commitment:
            # check the signature
            self.check_signature(
                self.wallet, self.sender_address,
                type_list=self._sign_type_list,
                value_list=[self.channel_name, nonce, self.payer_address, int(self.sender_balance),
                            self.payee_address, int(self.receiver_balance), sign_hashcode, sign_rcode],
                signature=self.commitment
            )

            # update this trade confirmed state
            Channel.update_trade(self.channel_name, nonce, commitment=commitment, peer_commitment=self.commitment,
                                 state=EnumTradeState.confirmed.name)
            need_update_balance = True

            rsmc_sign_body.update({'Commitment': commitment})

        # has resign response ??
        if resign_ack:
            rsmc_sign_body.update({'ResignBody': resign_ack})

        return need_update_balance, rsmc_sign_body

    def handle_founder_response(self):
        """

        :return:
        """
        need_update_balance = False
        # handle the resign body firstly
        resign_ack = None
        if self.resign_body:
            resign_ack, _ = self.handle_resign_body(self.wallet, self.channel_name, self.resign_body)

        sign_hashcode, sign_rcode = self.get_rcode(self.channel_name, self.hashcode)
        # has already signed by peer
        if self.commitment:
            # check the signature
            self.check_signature(
                self.wallet, self.sender_address,
                type_list=self._sign_type_list,
                value_list=[self.channel_name, self.nonce, self.payer_address, int(self.sender_balance),
                            self.payee_address, int(self.receiver_balance), sign_hashcode, sign_rcode],
                signature=self.commitment
            )
            # Just update current transaction confirmed:
            Channel.update_trade(self.channel_name, self.nonce, peer_commitment=self.commitment,
                                 state=EnumTradeState.confirmed.name)
            need_update_balance = True

            if self.comments:
                self.notify_peer_payment_finished()
        else:
            # to check the latest confirmed nonce
            confirmed_nonce = Channel.latest_confirmed_nonce(self.channel_name)
            if confirmed_nonce != self.nonce - 1:
                raise GoTo(
                    EnumResponseStatus.RESPONSE_TRADE_RESIGN_REQUEST_NOT_IMPLEMENTED,
                    'Wait for next resign. current confirmed nonce<{}>, request nonce<{}>'.format(confirmed_nonce,
                                                                                                  self.nonce)
                )

            # if running here, it means that the transaction has been succeeded to resign
            is_htlc_to_rsmc = self.is_hlock_to_rsmc(self.hashcode)
            self.check_balance(self.channel_name, self.asset_type, self.payer_address, self.sender_balance,
                               self.payee_address, self.receiver_balance, hlock_to_rsmc=is_htlc_to_rsmc, payment=self.payment)

            # sign this transaction
            commitment = RsmcResponsesMessage.sign_content(
                self.wallet, self._sign_type_list, [self.channel_name, self.nonce, self.payer_address, self.sender_balance,
                                                    self.payee_address, self.receiver_balance, sign_hashcode, sign_rcode]
            )

            # update the transaction confirming state
            Channel.update_trade(self.channel_name, self.nonce, balance=self.receiver_balance,
                                 peer_balance=self.sender_balance, commitment=commitment,
                                 state=EnumTradeState.confirming.name)

            rsmc_sign_body = self.response(self.asset_type, self.payment, self.sender_balance, self.receiver_balance,
                                           0, self.hashcode)
            rsmc_sign_body.update({'Commitment': commitment})

            return need_update_balance, rsmc_sign_body

        return need_update_balance, None
