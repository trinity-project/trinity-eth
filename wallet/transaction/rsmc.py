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
from .payment import Payment

from common.log import LOG
from common.common import uri_parser
from common.exceptions import GoTo, GotoIgnore
from wallet.channel import Channel
from wallet.channel import EnumTradeType, EnumTradeRole, EnumTradeState


class RsmcMessage(Message):
    """
    {
        "MessageType":"Rsmc",
        "Sender": sender,
        "Receiver": receiver,
        "TxNonce": nonce,
        "ChannelName":channel_name,
        "NetMagic": RsmcMessage.get_magic(),
        "AssetType":asset_type.upper(),
        "MessageBody": {
            "PaymentCount": payment,
            "SenderBalance": sender_balance,
            "ReceiverBalance": receiver_balance
        }
        "Comments": {}
    }
    """
    _message_name = 'Rsmc'

    def __init__(self, message, wallet=None):
        super().__init__(message)

        self.payment = self.message_body.get("PaymentCount")
        self.sender_balance = self.message_body.get("SenderBalance")
        self.receiver_balance = self.message_body.get("ReceiverBalance")

        self.wallet = wallet
        self.rsmc_sign_role = 0

    def handle_message(self):
        self.handle()

    def handle(self):
        super(RsmcMessage, self).handle()

        status = EnumResponseStatus.RESPONSE_FAIL
        try:
            self.check_channel_state(self.channel_name)

            verified, error = self.verify()
            if not verified:
                status = EnumResponseStatus.RESPONSE_TRADE_VERIFIED_ERROR
                raise GoTo('Verify RsmcMessage error: {}'.format(error))

            verified, error = self.verify_channel_balance(self.sender_balance, self.receiver_balance, self.payment)
            if not verified:
                status = EnumResponseStatus.RESPONSE_TRADE_BALANCE_ERROR
                raise GoTo('Verify balance error: {}'.format(error))

            RsmcResponsesMessage.create(self.channel_name, self.wallet, self.sender, self.receiver,
                                        self.payment, self.sender_balance, self.receiver_balance,
                                        self.nonce, self.rsmc_sign_role, self.asset_type, comments=self.comments)

            # means the response ok is sent
            status = EnumResponseStatus.RESPONSE_OK
        except GoTo as error:
            LOG.error(error)
        except Exception as error:
            LOG.error('Failed to handle RsmcMessage. Exception: {}'.format(error))
        finally:
            if EnumResponseStatus.RESPONSE_OK != status:
                # nofify error response
                RsmcResponsesMessage.send_error_response(self.sender, self.receiver, self.channel_name, self.asset_type,
                                                         self.nonce, status)

        return

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
        # channel
        channel = Channel(channel_name)
        # check state
        if not channel.is_opened:
            raise GoTo('Channel<{}> is not OPENED. State: {}.'.format(channel_name, channel.state))

        # get nonce in the offline account book
        nonce = Channel.new_nonce(channel_name)
        if RsmcMessage._FOUNDER_NONCE > nonce:
            raise GoTo('RsmcMessage::create: Incorrect nonce<{}> for channel<{}>'.format(nonce, channel_name))

        # to get channel balance
        if not channel.balance:
            raise GoTo('Void balance<{}> for asset <{}>.'.format(channel.balance, asset_type))
        balance = channel.balance

        payment = float(payment)
        sender_address, _, _ = uri_parser(sender)
        receiver_address, _, _ = uri_parser(receiver)
        asset_type = asset_type.upper()

        # check balance is enough
        checked, sender_balance = RsmcMessage.check_payment(channel_name, sender_address, asset_type, payment)
        if not checked:
            raise GoTo('RsmcMessage::create: Payment<{}> should be satisfied 0 < payment <= {}'.format(payment,
                                                                                                       sender_balance))
        sender_balance = RsmcMessage.float_calculate(sender_balance, payment, False)
        receiver_balance = RsmcMessage.float_calculate(balance.get(receiver_address, {}).get(asset_type, 0), payment)

        # # sender sign
        # commitment = RsmcMessage.sign_content(
        #     typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
        #     valueList=[channel_name, nonce, sender_address, sender_balance, receiver_address, receiver_balance],
        #     privtKey = wallet._key.private_key_string)
        #
        # # TODO: MUST record this commitment and balance info
        # # add trade to database
        # # ToDo: need re-sign all unconfirmed htlc message later
        # rsmc_trade = Channel.founder_or_rsmc_trade(
        #     role=EnumTradeRole.TRADE_ROLE_FOUNDER, asset_type=asset_type, payment=payment,
        #     balance=sender_balance, peer_balance=receiver_balance,
        #     commitment=commitment, state=EnumTradeState.confirming
        # )
        # Channel.add_trade(channel_name, nonce=nonce, rsmc=rsmc_trade)

        message_body = {
            "AssetType":asset_type.upper(),
            "PaymentCount": payment,
            "SenderBalance": sender_balance,
            "ReceiverBalance": receiver_balance,
        }

        # start to create message
        message = RsmcMessage.create_message_header(sender, receiver, RsmcMessage._message_name,
                                                    channel_name, asset_type, nonce)
        message = message.message_header
        message.update({'MessageBody': message_body})
        if comments:
            message.update({"Comments": comments})

        RsmcMessage.send(message)

        return None

    def verify(self):
        verified, error = super(RsmcMessage, self).verify()
        if not verified:
            return verified, error

        if Message._FOUNDER_NONCE >= int(self.nonce):
            return False, 'Nonce MUST be larger than zero'

        verified, balance = self.check_payment(self.channel_name, self.sender_address, self.asset_type, self.payment)
        if not verified:
            return verified, \
                   'RsmcMessage::verify: Payment<{}> should be satisfied 0 < payment <= {}'.format(self.payment,
                                                                                                   balance)

        return True, None


class RsmcResponsesMessage(Message):
    """
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
        "Comments": {},
        "Status":
    }
    """
    _message_name = 'RsmcSign'

    def __init__(self, message, wallet):
        super(RsmcResponsesMessage, self).__init__(message)

        self.channel = Channel(self.channel_name)

        self.payment = self.message_body.get("PaymentCount")
        self.sender_balance = self.message_body.get("SenderBalance")
        self.receiver_balance = self.message_body.get("ReceiverBalance")
        self.commitment = self.message_body.get('Commitment')
        self.role_index = int(self.message_body.get('RoleIndex', 0xFF))
        self.wallet = wallet

        self.rsmc_sign_role = 1

    def handle_message(self):
        self.handle()

    def handle(self):
        super(RsmcResponsesMessage, self).handle()

        status = EnumResponseStatus.RESPONSE_FAIL
        try:
            self.check_channel_state(self.channel_name)

            verified, error = self.verify()
            if not verified:
                status = EnumResponseStatus.RESPONSE_TRADE_VERIFIED_ERROR
                raise GoTo(error)

            if 0 == self.role_index:
                self.create(self.channel_name, self.wallet, self.sender, self.receiver, self.payment,
                            self.sender_balance, self.receiver_balance, self.nonce, role_index=1,
                            asset_type=self.asset_type)
            else:
                checked, sender_balance = self.check_payment(self.channel_name, self.sender_address,
                                                             self.asset_type, self.payment)
                if not checked:
                    status = EnumResponseStatus.RESPONSE_TRADE_INCORRECT_PAYMENT
                    raise GoTo('RsmcResponsesMessage::handle: Payment<{}> should be satisfied 0 < payment <= {}'.format(self.payment,
                                                                                                               sender_balance))

                # check nonce here for role index = 1
                nonce = Channel.latest_nonce(self.channel_name)
                if Message._FOUNDER_NONCE < nonce != self.nonce:
                    status = EnumResponseStatus.RESPONSE_TRADE_INCOMPATIBLE_NONCE
                    raise GoTo('Incompatible nonce. self:<{}>, peer<{}>'.format(nonce, self.nonce))

            #
            # update transaction
            trade_rsmc = Channel.query_trade(self.channel_name, self.nonce)[0]
            if not (trade_rsmc and trade_rsmc.rsmc):
                status = EnumResponseStatus.RESPONSE_TRADE_NOT_FOUND
                raise GoTo('Not found the trade transaction for channel<{}>, nonce<{}>, role_index'.format(self.channel_name,
                                                                                                           self.nonce,
                                                                                                           self.role_index))

            trade_rsmc = trade_rsmc.rsmc
            trade_rsmc.update({'peer_commitment': self.commitment, 'state': EnumTradeState.confirmed.name})
            Channel.update_trade(self.channel_name, self.nonce, rsmc=trade_rsmc)

            # update the channel balance
            if float(self.sender_balance) >= 0 and float(self.receiver_balance) >= 0:
                Channel.update_channel(self.channel_name,
                                       balance={self.sender_address: {self.asset_type: self.sender_balance},
                                                self.receiver_address: {self.asset_type: self.receiver_balance}})

            status = EnumResponseStatus.RESPONSE_OK

            # update payment after response OK
            if 1 == self.role_index:
                Payment.confirm_payment(self.channel, self.comments, self.payment)
        except GoTo as error:
            LOG.error(error)
        except Exception as error:
            status = EnumResponseStatus.RESPONSE_EXCEPTION_HAPPENED
            LOG.error('Failed to handle RsmcSign for channel<{}> '.format(self.channel_name),
                      'nonce<{}>, role_index<{}>.'.format(self.nonce, self.role_index),
                      'Exception: {}'.format(error))
        finally:
            # send error response
            if EnumResponseStatus.RESPONSE_OK != status:
                if 0 == self.role_index:
                    self.send_error_response(self.sender, self.receiver, self.channel_name,
                                             self.asset_type, self.nonce, status)

                # need rollback some resources
                self.rollback_resource(self.channel_name, self.nonce, status=self.status)

        return

    @staticmethod
    def create(channel_name, wallet, sender, receiver, payment, sender_balance, receiver_balance, tx_nonce,
               role_index=0, asset_type="TNC", cli=False, comments=None):
        """

        :param channel_name:
        :param wallet:
        :param sender:
        :param receiver:
        :param payment:
        :param asset_type:
        :param role_index:
        :param cli:
        :param comments:
        :return:
        """
        LOG.debug('#################balance: sender_balance<{}>, receiver_balance<{}>'.format(sender_balance, receiver_balance))
        # get channel by channel name
        channel = Channel(channel_name)
        if not channel.is_opened:
            raise GoTo('RsmcResponsesMessage::create: Channel<{}> is not OPENED. State: {}.'.format(channel_name, channel.state))

        # get latest nonce
        checked, nonce = RsmcResponsesMessage.check_nonce(channel_name, tx_nonce)
        if not checked:
            raise GoTo('RsmcResponsesMessage::create: channel<{}>'.format(channel_name),
                       'Incompatible nonce! self<{}>, peer<{}> for role index<{}>'.format(nonce, tx_nonce, role_index))

        asset_type = asset_type.upper()

        # different ROLE by role index
        role_index = int(role_index)
        if 0 == role_index:
            # get address from uri
            sender_address, _, _ = uri_parser(sender)
            receiver_address, _, _ = uri_parser(receiver)
            trade_role = EnumTradeRole.TRADE_ROLE_PARTNER
        elif 1 == role_index:
            # get address from uri
            sender_address, _, _ = uri_parser(receiver)
            receiver_address, _, _ = uri_parser(sender)
            trade_role = EnumTradeRole.TRADE_ROLE_FOUNDER
        else:
            raise GoTo('Incorrect role index<{}>'.format(role_index))

        # check balance is enough
        checked, self_balance = RsmcResponsesMessage.check_payment(channel_name, sender_address, asset_type, payment)
        if not checked:
            raise GoTo('RsmcResponsesMessage::create: Payment<{}> should be satisfied 0 < payment <= {}'.format(payment,
                                                                                                                self_balance))

        # calculate the balance
        balance = channel.balance
        self_balance = RsmcResponsesMessage.float_calculate(self_balance, payment, False)
        peer_balance = RsmcResponsesMessage.float_calculate(balance.get(receiver_address, {}).get(asset_type, 0), payment)
        LOG.debug('#################balance: self<{}>, receiver<{}>'.format(self_balance, peer_balance))

        # sign the trade
        commitment = RsmcResponsesMessage.sign_content(
            typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
            valueList=[channel_name, nonce, sender_address, self_balance, receiver_address, peer_balance],
            privtKey = wallet._key.private_key_string)

        # # just record the payment for the partner
        # # ToDo: uncomment here if needed.
        # if RsmcResponsesMessage.hashr_is_valid_format(comments):
        #     channel.add_payment(channel_name, hashcode=comments, payment=payment, state=EnumTradeState.confirming)

        # add trade to database
        # ToDo: need re-sign all unconfirmed htlc message later
        rsmc_trade = Channel.founder_or_rsmc_trade(
            role=trade_role, asset_type=asset_type, payment=payment,
            balance=self_balance, peer_balance=peer_balance,
            commitment=commitment, state=EnumTradeState.confirming
        )
        Channel.add_trade(channel_name, nonce=nonce, rsmc=rsmc_trade)

        # update message body
        message_body = {
            "AssetType": asset_type.upper(),
            "PaymentCount": str(payment),
            "SenderBalance": str(self_balance),
            "ReceiverBalance": str(peer_balance),
            "Commitment": commitment,
            "RoleIndex": str(role_index),
        }

        # generate the message header
        message = RsmcResponsesMessage.create_message_header(receiver, sender, RsmcResponsesMessage._message_name,
                                                             channel_name, asset_type, nonce)
        message = message.message_header

        # to send response OK message
        message.update({'MessageBody': message_body})
        message.update({'Status': EnumResponseStatus.RESPONSE_OK.name})
        if comments:
            message.update({"Comments": comments})

        # send RsmcSign message
        RsmcResponsesMessage.send(message)

        return

    def verify(self):
        verified, error = super(RsmcResponsesMessage, self).verify()
        if not verified:
            return verified, error

        if EnumResponseStatus.RESPONSE_OK.name != self.status:
            return False, self.status

        if self.role_index not in [0, 1]:
            return False, 'RsmcSign with illegal role index<{}>'.format(self.role_index)
        return True, None
