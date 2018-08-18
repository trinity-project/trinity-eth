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
from wallet.event.contract_event import contract_event_api


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

        try:
            verified, error = self.verify()
            if not verified:
                raise GoTo('Handle RsmcMessage error: {}'.format(error))

            RsmcMessage.check_payment(self.payment)

            verified, error = self.verify_channel_balance(self.sender_balance+self.payment,
                                                          self.receiver_balance-self.payment)
            if not verified:
                raise GoTo('Verify balance error: {}'.format(error))

            RsmcResponsesMessage.create(self.channel_name, self.wallet, self.sender, self.receiver,
                                        self.payment, self.sender_balance, self.receiver_balance,
                                        self.nonce, self.rsmc_sign_role, self.asset_type, comments=self.comments)
        except GoTo as error:
            LOG.error(error)
        except Exception as error:
            LOG.error('Failed to andle RsmcMessage. Exception: {}'.format(error))
            return
        finally:
            pass

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
        channel = Channel(channel_name)

        try:
            # get transaction history
            transaction = channel.latest_trade(channel_name)
            # get nonce in the offline account book
            if not transaction:
                raise GoTo('Could not find the trade history. Why!')
            nonce = int(transaction.nonce) + 1

            message = RsmcMessage.create_message_header(sender, receiver, RsmcMessage._message_name,
                                                        channel_name, asset_type, nonce)
            message = message.message_header

            if not channel.balance:
                raise GoTo('Void balance<{}> for asset <{}>.'.format(channel.balance, asset_type))
            balance = channel.balance

            sender_address, _, _ = uri_parser(sender)
            receiver_address, _, _ = uri_parser(receiver)
            asset_type = asset_type.upper()
            payment = float(payment)
            RsmcMessage.check_payment(payment)

            sender_balance = RsmcMessage.float_calculate(balance.get(sender_address, {}).get(asset_type, 0), payment, False)
            if sender_balance < 0:
                raise GoTo('Sender balance is not enough for payment {}. sender_balance: {}'.format(payment,
                                                                                                    balance.get(sender_address)))

            receiver_balance = RsmcMessage.float_calculate(balance.get(receiver_address, {}).get(asset_type, 0), payment)

            # sender sign
            commitment = contract_event_api.sign_content(
                typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
                valueList=[channel_name, nonce, sender_address, sender_balance, receiver_address, receiver_balance],
                privtKey = wallet._key.private_key_string)

            # TODO: MUST record this commitment and balance info
            # add trade to database
            # ToDo: need re-sign all unconfirmed htlc message later
            rsmc_trade = Channel.founder_or_rsmc_trade(
                role=EnumTradeRole.TRADE_ROLE_FOUNDER, asset_type=asset_type, payment=payment,
                balance=sender_balance, peer_balance=receiver_balance,
                commitment=commitment, state=EnumTradeState.confirming
            )
            Channel.add_trade(channel_name, nonce=nonce, rsmc=rsmc_trade)

            message_body = {
                "AssetType":asset_type.upper(),
                "PaymentCount": payment,
                "SenderBalance": sender_balance,
                "ReceiverBalance": receiver_balance,
                "Commitment": commitment
            }
        except GoTo as error:
            LOG.error(error)
        except Exception as error:
            LOG.exception('Create Rsmc message error: {}'.format(error))
            if cli:
                print(error)
        else:
            message.update({'MessageBody': message_body})
            if comments:
                message.update({"Comments": comments})

            RsmcMessage.send(message)

            return message

        return None

    def verify(self):
        verified, error = super(RsmcMessage, self).verify()
        if not verified:
            return verified, error

        # if 0 >= int(self.nonce):
        #     return False, 'Nonce MUST be larger than zero'
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

        try:
            verified, error = self.verify()
            if not verified:
                raise GoTo(error)

            RsmcResponsesMessage.check_payment(self.payment)
            
            if 0 == self.role_index:
                status = self.create(self.channel_name, self.wallet, self.sender, self.receiver, self.payment,
                                     self.sender_balance, self.receiver_balance, self.nonce, role_index=1,
                                     asset_type=self.asset_type)
                if EnumResponseStatus.RESPONSE_OK != status:
                    raise GoTo('RsmcSign with role index<1> has wrong response status<{}>'.format(status))

            # update transaction
            trade_rsmc = Channel.query_trade(self.channel_name, self.nonce)[0]
            if not (trade_rsmc and trade_rsmc.rsmc):
                raise GoTo('Not found the trade transaction for channel<{}>, nonce<{}>, role_index'.format(self.channel_name,
                                                                                                           self.nonce,
                                                                                                           self.role_index))
            trade_rsmc = trade_rsmc.rsmc
            trade_rsmc.update({'peer_commitment': self.commitment, 'state': EnumTradeState.confirmed.name})
            Channel.update_trade(self.channel_name, self.nonce, rsmc=trade_rsmc)

            # update the channel balance
            if self.sender_balance and self.receiver_balance:
                Channel.update_channel(self.channel_name,
                                       balance={self.sender_address: {self.asset_type: self.sender_balance},
                                                self.receiver_address: {self.asset_type: self.receiver_balance}})

        except GoTo as error:
            LOG.error(error)
        except Exception as error:
            LOG.exception('Failed to handle RsmcSign for channel<{}> '.format(self.channel_name),
                          'nonce<{}>, role_index<{}>.'.format(self.nonce, self.role_index),
                          'Exception: {}'.format(error))

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
        # generate the message header
        message = RsmcResponsesMessage.create_message_header(receiver, sender, RsmcResponsesMessage._message_name,
                                                             channel_name, asset_type, tx_nonce)
        message = message.message_header

        # initialize some local variables
        status = EnumResponseStatus.RESPONSE_OK
        message_body = {"RoleIndex": role_index}
        commitment=None
        nonce=tx_nonce

        # get channel by channel name
        channel = Channel(channel_name)
        try:
            # get transaction history
            transaction = channel.latest_trade(channel_name)
            # get nonce in the offline account book
            if not transaction:
                status = EnumResponseStatus.RESPONSE_TRADE_MISSING_IN_DB
                raise GoTo('No trade was recorded for channel<{}>'.format(channel_name))

            # to get the data to organize the RSMC response message for role index = 1
            if 1 == role_index:
                rsmc_trade = transaction.rsmc
                if EnumTradeRole.TRADE_ROLE_FOUNDER.name !=  rsmc_trade.get('role'):
                    status = EnumResponseStatus.RESPONSE_TRADE_INCORRECT_ROLE
                    raise GoTo('Trade role is error in the database for channel<{}> in side {}'.format(channel_name, receiver))
                message_body = {
                    "AssetType": rsmc_trade.get('asset_type'),
                    "PaymentCount": rsmc_trade.get('payment'),
                    "SenderBalance": rsmc_trade.get('balance'),
                    "ReceiverBalance": rsmc_trade.get('peer_balance'),
                    "Commitment": rsmc_trade.get('commitment'),
                    "RoleIndex": role_index
                }
                raise GotoIgnore('RsmcSign use data from database.')
            nonce = int(transaction.nonce) + 1
            message.update({'TxNonce': nonce})
            # check the validity of the nonce
            if nonce != tx_nonce:
                status = EnumResponseStatus.RESPONSE_TRADE_INCOMPATIBLE_NONCE
                raise GoTo('Incompatible nonce<self: {}, peer: {}> for channel<{}>'.format(nonce, tx_nonce, channel_name))

            #
            sender_address, _, _ = uri_parser(sender)
            receiver_address, _, _ = uri_parser(receiver)
            asset_type = asset_type.upper()
            balance = channel.balance

            # sign the trade
            commitment = contract_event_api.sign_content(
                typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
                valueList=[channel_name, nonce, sender_address, sender_balance, receiver_address, receiver_balance],
                privtKey = wallet._key.private_key_string)

            message_body = {
                "AssetType": asset_type.upper(),
                "PaymentCount": str(payment),
                "SenderBalance": str(receiver_balance),
                "ReceiverBalance": str(sender_balance),
                "Commitment": commitment,
                "RoleIndex": str(role_index),
            }

            # just record the payment when first RsmcSign
            if RsmcResponsesMessage.hashr_is_valid_format(comments):
                channel.add_payment(channel_name, hashcode=comments, payment=payment, state=EnumTradeState.confirming)

        except GoTo as error:
            LOG.error(error)
        except GotoIgnore as error:
            pass
        except Exception as error:
            LOG.error('Exception when creating RsmcSign message. Exception: {}'.format(error))
            status = EnumResponseStatus.RESPONSE_EXCEPTION_HAPPENED
        finally:
            if 0 == role_index:
                if status == EnumResponseStatus.RESPONSE_OK:
                    # update the payment history
                    Payment.confirm_payment(channel_name, comments, payment)
                # for keep compatible nonce, need add trade heer
                # add trade to database
                # ToDo: need re-sign all unconfirmed htlc message later
                rsmc_trade = Channel.founder_or_rsmc_trade(
                    role=EnumTradeRole.TRADE_ROLE_PARTNER, asset_type=asset_type, payment=payment,
                    balance=receiver_balance, peer_balance=sender_balance,
                    commitment=commitment, state=EnumTradeState.confirming
                )
                Channel.add_trade(channel_name, nonce=nonce, rsmc=rsmc_trade)

            message.update({'MessageBody': message_body})
            message.update({'Status': status.name})

            if comments:
                message.update({"Comments": comments})

            # send RsmcSign message
            RsmcResponsesMessage.send(message)

        return status

    def verify(self):
        verified, error = super(RsmcResponsesMessage, self).verify()
        if not verified:
            return verified, error

        if EnumResponseStatus.RESPONSE_OK.name != self.status:
            return False, 'RsmcSign status error: {}'.format(self.status)

        if self.role_index not in [0, 1]:
            return False, 'RsmcSign with illegal role index<{}>'.format(self.role_index)
        return True, None
