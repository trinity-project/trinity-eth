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
from .payment import Payment

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
    def get_payer_and_payee(cls, role_index, sender, receiver):
        """

        :param role_index:
        :param sender:
        :param receiver:
        :return:
        """
        role = int(role_index)
        cls.check_role(role)

        # reverse the sender and receiver by role
        if 0 == role:
            return receiver, sender
        else:
            return sender, receiver

    @classmethod
    def check_role(cls, role):
        # row index related check
        if int(role) not in [0, 1]:
            raise GoTo(EnumResponseStatus.RESPONSE_TRADE_INCORRECT_ROLE,
                       'RsmcSign with illegal role index<{}>'.format(role))

        return True


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

    def handle_message(self):
        self.handle()

    def handle(self):
        super(RsmcMessage, self).handle()

        status = EnumResponseStatus.RESPONSE_OK
        try:
            # send RsmcSign message to peer
            RsmcResponsesMessage.create(self.wallet, self.channel_name, self.asset_type, self.nonce, self.net_magic,
                                        self.sender, self.receiver, self.payment, self.sender_balance,
                                        self.receiver_balance, self.rsmc_sign_role, self.hashcode, self.comments)

            APIStatistics.update_statistics(self.wallet.address, rsmc='rsmc')
        except TrinityException as error:
            status = error.reason
            LOG.error(error)
        except Exception as error:
            status = EnumResponseStatus.RESPONSE_EXCEPTION_HAPPENED
            LOG.error('Failed to handle RsmcMessage. Exception: {}'.format(error))
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

        # get nonce in the offline account book
        nonce = Channel.new_nonce(channel_name)
        if RsmcMessage._FOUNDER_NONCE > nonce:
            raise GoTo(EnumResponseStatus.RESPONSE_TRADE_WITH_INCORRECT_NONCE,
                       'RsmcMessage::create: Incorrect nonce<{}> for channel<{}>'.format(nonce, channel_name))

        # to get channel balance
        balance = channel.balance
        payer_address, _, _ = uri_parser(sender)
        payee_address, _, _ = uri_parser(receiver)
        asset_type = asset_type.upper()

        # judge whether it is htlc lock part to rsmc trade or not
        hlock_to_rsmc = RsmcMessage.is_hlock_to_rsmc(hashcode)
        _, payer_balance, payee_balance = RsmcBase.calculate_balance_after_payment(
            balance.get(payer_address).get(asset_type), balance.get(payee_address).get(asset_type), payment,
            hlock_to_rsmc=hlock_to_rsmc)

        APIStatistics.update_statistics(payer_address, rsmc='rsmc')

        # create message
        message_body = {
            'AssetType':asset_type.upper(),
            'PaymentCount': str(payment),
            'SenderBalance': str(payer_balance),
            'ReceiverBalance': str(payee_balance),
        }

        if hlock_to_rsmc:
            message_body.update({'HashR': hashcode})

        # start to create message
        message = RsmcMessage.create_message_header(sender, receiver, RsmcMessage._message_name,
                                                    channel_name, asset_type, nonce)
        message = message.message_header
        message.update({'MessageBody': message_body})
        if comments:
            message.update({'Comments': comments})

        RsmcMessage.send(message)

        return None

    @classmethod
    def get_payer_and_payee(cls, role_index, sender, receiver):
        return super(RsmcMessage, cls).get_payer_and_payee(role_index, receiver, sender)

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
        self.payer, self.payee = self.get_payer_and_payee(self.role_index, self.sender_address, self.receiver_address)

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
            nonce = self.nonce if 0 == self.role_index else self.nonce + 1 # this is just used for check nonce
            self.check_nonce(nonce, self.channel_name)

            is_htlc_to_rsmc = self.is_hlock_to_rsmc(self.hashcode)
            self.check_balance(self.channel_name, self.asset_type, self.payer, self.sender_balance,
                               self.payee, self.receiver_balance, hlock_to_rsmc=is_htlc_to_rsmc, payment=self.payment)

            sign_hashcode, sign_rcode = self.get_rcode(self.channel_name, self.hashcode)
            self.check_signature(
                self.wallet, self.sender_address,
                type_list=self._sign_type_list,
                value_list=[self.channel_name, self.nonce, self.payer, int(self.sender_balance),
                            self.payee, int(self.receiver_balance), sign_hashcode, sign_rcode],
                signature=self.commitment
            )

            if 0 == self.role_index:
                self.rsmc_sign(self.wallet, self.channel_name, self.asset_type, self.nonce, self.sender, self.receiver,
                               self.payment, self.sender_balance, self.receiver_balance, self.rsmc_sign_role,
                               self.hashcode, self.comments)
            
            # update transaction
            Channel.update_trade(self.channel_name, self.nonce, peer_commitment=self.commitment,
                                 state=EnumTradeState.confirmed.name)

            if 0 == self.role_index:
                APIStatistics.update_statistics(self.wallet.address, payment=self.payment, payer=True)
            else:
                APIStatistics.update_statistics(self.wallet.address, payment=self.payment, payer=False)

            Channel.confirm_payment(self.channel_name, self.hashcode, is_htlc_to_rsmc)

            # update the channel balance
            self.update_balance_for_channel(self.channel_name, self.asset_type, self.payer, self.payee, self.payment,
                                            is_htlc_to_rsmc)
        except GoTo as error:
            LOG.error(error)
            status = error.reason
        except Exception as error:
            status = EnumResponseStatus.RESPONSE_EXCEPTION_HAPPENED
            LOG.error('Failed to handle RsmcSign for channel<{}> nonce<{}>, role_index<{}>.Exception: {}' \
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

    @classmethod
    def rsmc_sign(cls, wallet, channel_name, asset_type, nonce, sender, receiver, payment,
                  sender_balance, receiver_balance, role_index=0, hashcode=None, comments=None):
        """
        Descriptions: create and send RsmcSign messages.
        :param wallet:
        :param channel_name:
        :param asset_type:
        :param nonce:
        :param sender:
        :param receiver:
        :param payment:
        :param sender_balance:
        :param receiver_balance:
        :param role_index:
        :param comments:
        :param hashcode:
        :return:
        """
        asset_type = asset_type.upper()

        # different ROLE by role index
        role_index = int(role_index)
        payer, payee = RsmcMessage.get_payer_and_payee(role_index, sender, receiver)
        payer_address, _, _ = uri_parser(payer)
        payee_address, _, _ = uri_parser(payee)

        # check balance
        is_hlock_to_rsmc = RsmcResponsesMessage.is_hlock_to_rsmc(hashcode)
        _, payer_balance, payee_balance = RsmcResponsesMessage.check_balance(
            channel_name, asset_type, payer_address, sender_balance, payee_address, receiver_balance,
            hlock_to_rsmc=is_hlock_to_rsmc, payment=payment
        )

        # sign the trade
        sign_hashcode, sign_rcode = cls.get_rcode(channel_name, hashcode)
        commitment = RsmcResponsesMessage.sign_content(
            typeList=RsmcResponsesMessage._sign_type_list,
            valueList=[channel_name, nonce, payer_address, payer_balance, payee_address, payee_balance,
                       sign_hashcode, sign_rcode],
            privtKey = wallet._key.private_key_string)


        # add trade to database
        if 0 == role_index:
            trade_role = EnumTradeRole.TRADE_ROLE_PARTNER
            self_balance = payee_balance
            peer_balance = payer_balance
        else:
            trade_role = EnumTradeRole.TRADE_ROLE_FOUNDER
            self_balance = payer_balance
            peer_balance = payee_balance

        # ToDo: need re-sign all unconfirmed htlc message later
        rsmc_trade = Channel.rsmc_trade(
            type=EnumTradeType.TRADE_TYPE_RSMC, role=trade_role, asset_type=asset_type,
            balance=self_balance, peer_balance=peer_balance, payment=payment,
            hashcode=sign_hashcode, rcode=sign_rcode, commitment=commitment)
        Channel.add_trade(channel_name, nonce=nonce, **rsmc_trade)

        # update message body
        message_body = {
            'AssetType': asset_type.upper(),
            'PaymentCount': str(payment),
            'SenderBalance': str(payer_balance),
            'ReceiverBalance': str(payee_balance),
            'Commitment': commitment,
            'RoleIndex': str(role_index),
        }

        if hashcode:
            message_body.update({'HashR': hashcode})

        # generate the message header
        message = RsmcResponsesMessage.create_message_header(receiver, sender, RsmcResponsesMessage._message_name,
                                                             channel_name, asset_type, nonce)
        message = message.message_header

        # to send response OK message
        message.update({'MessageBody': message_body})
        message.update({'Status': EnumResponseStatus.RESPONSE_OK.name})
        if comments:
            message.update({'Comments': comments})

        # send RsmcSign message
        RsmcResponsesMessage.send(message)

        return

    @staticmethod
    def create(wallet, channel_name, asset_type, tx_nonce, network_magic, sender, receiver, payment,
               sender_balance, receiver_balance, role_index=0, hashcode=None, comments=None, cli=False):
        """
        Descriptions: RsmcSign API called by other classes
        :param cli:
        :param Other parameters could refer to details of rsmc_sign
        :return:
        """
        # some common checks, such as channe state, role_index, etc.
        RsmcResponsesMessage.check_channel_state(channel_name)
        RsmcResponsesMessage.common_check(sender, receiver, asset_type, network_magic)
        RsmcResponsesMessage.check_nonce(tx_nonce, channel_name)

        RsmcResponsesMessage.rsmc_sign(wallet, channel_name, asset_type, tx_nonce, sender, receiver, payment,
                                       sender_balance, receiver_balance, role_index, hashcode, comments)

        return
