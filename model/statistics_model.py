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
from .manager import DBManager, rpc_response, connection_singleton
from .base_enum import EnumAssetType, EnumChannelState
from common.log import LOG


class TBLStatistics(DBManager):
    """
        Descriptions    :
        Created         : 2018-02-13
        Modified        : 2018-03-21
    """
    def add_one(self, address: str):

        return super(TBLStatistics, self).add(address=address, total_channel=0, opend_channel=0,
                                           settled_channel=0,closed_channel=0,
                                           total_rsmc_transaction=0, rsmc_successed=0,payment=0,income=0,
                                           total_htlc_transaction=0, htlc_successed=0,total_free=0)

    def update(self, address, **kwargs):

        keys = kwargs.keys()
        if 'state' in keys:
            state = kwargs.pop('state', None)

            if state == EnumChannelState.INIT.name:
                kwargs.update({'total_channel': 1})

            elif state == EnumChannelState.OPENED.name:
                kwargs.update({'opend_channel': 1})

            elif state == EnumChannelState.SETTLED.name:
                kwargs.update({'settled_channel': 1})
                kwargs.update({'opend_channel': -1})

            elif state == EnumChannelState.CLOSED.name:
                kwargs.update({'closed_channel': 1})
                kwargs.update({'opend_channel': -1})

        elif 'rsmc' in keys:
            kwargs.pop('rsmc', None)
            kwargs.update({'total_rsmc_transaction': 1})

        elif 'payment' in keys and 'payer' in keys:
            payment = kwargs.pop('payment', 0)
            payer = kwargs.pop('payer', False)
            is_htlc_to_rsmc = kwargs.pop('is_htlc_to_rsmc', False)

            if payer:
                kwargs.update({'payment': int(payment)})
            else:
                kwargs.update({'income': int(payment)})

            kwargs.update({'rsmc_successed': 1})

        elif 'htlc_free' in keys:
            free = kwargs.pop('htlc_free', 0)
            kwargs.update({'total_htlc_transaction': 1})
            kwargs.update({'total_free': free})

        elif 'htlc_rcode' in keys:
            kwargs.pop('htlc_rcode', True)
            kwargs.update({'htlc_successed': 1})

        return  super(TBLStatistics, self).update_ont_statistics(address, **kwargs)


    def remove_unsupported_asset(self, asset):
        if not asset:
            return True

        try:
            for asset_type in asset.keys():
                if not self.is_valid_asset_type(asset_type):
                    asset.pop(asset_type)
        except Exception as exp_info:
            LOG.error('Error asset of users. Asset: {}'.format(asset))
            return False

        return True

    @staticmethod
    def is_valid_channel_state(state):
        return state.upper() in EnumChannelState.__members__

    @staticmethod
    def is_valid_asset_type(asset_type):
        return asset_type.upper() in EnumAssetType.__members__

    @property
    @connection_singleton
    def client(self):
        return super(TBLStatistics, self).client

    @property
    def db_table(self):
        return self.client.db.Statistics

    @property
    def primary_key(self):
        return 'address'

    @property
    def required_item(self):
        return ['address',
                'total_channel', 'opend_channel', 'settled_channel', 'closed_channel',
                'total_transaction', 'expenditure', 'revenue']


class APIStatistics(object):
    table = TBLStatistics()

    @classmethod
    def add_statistics(cls, address):
        return cls.table.add_one(address)

    @classmethod
    def query_statistics(cls, address, *args, **kwargs):
        return cls.table.query_one(address, *args, **kwargs)

    @classmethod
    def batch_query_statistics(cls, filters, *args, **kwargs):
        return cls.table.query_many(filters, *args, **kwargs)

    @classmethod
    def update_statistics(cls, address, **kwargs):
        return cls.table.update(address, **kwargs)

    @classmethod
    def batch_update_statistics(cls, filters, **kwargs):
        return cls.table.update_many(filters, **kwargs)
