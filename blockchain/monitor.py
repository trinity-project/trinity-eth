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
import time
from wallet.event import event_machine
from blockchain.interface import get_block_count
from wallet.event.chain_event import ws_instance


class EventMonitor(object):
    GoOn = True
    Wallet = None
    Wallet_Change = False
    BlockHeight = None
    BlockPause = False

    @classmethod
    def stop_monitor(cls):
        cls.GoOn = False

    @classmethod
    def start_monitor(cls, wallet):
        cls.Wallet = wallet
        cls.Wallet_Change = True

        if wallet:
            try:
                ws_instance.set_wallet(wallet)
                ws_instance.notify_wallet_info()
            except Exception as error:
                print('No wallet is opened')
                pass

    @classmethod
    def update_wallet_block_height(cls, height):
        if cls.Wallet_Change:
            cls.Wallet_Change = False
            return None

        if cls.Wallet:
            cls.Wallet.BlockHeight=height
        else:
            return None

    @classmethod
    def get_wallet_block_height(cls):
        if cls.Wallet:
            block_height = cls.Wallet.BlockHeight
            cls.Wallet_Change = False
            return block_height if block_height else 1
        else:
            return 1

    @classmethod
    def update_block_height(cls, blockheight):
        cls.BlockHeight = blockheight

    @classmethod
    def get_block_height(cls):
        return cls.BlockHeight if cls.BlockHeight else 1


def monitorblock():
    """"""
    old_blockheight_onchain = 0
    while EventMonitor.GoOn:
        blockheight_onchain = get_block_count()
        EventMonitor.update_block_height(blockheight_onchain)
        blockheight = EventMonitor.get_wallet_block_height()
        block_delta = int(blockheight_onchain) - int(blockheight) if 1 != blockheight else 0
        need_update = block_delta > 0
        execute_event_machine = old_blockheight_onchain != blockheight_onchain

        # reset event machine
        event_machine.reset_polling()

        end_time = time.time() + 15 # sleep 15 second according to the chain update block time
        trigger_per_block = False
        while True:
            try:
                if 0 < block_delta < 2010:
                    if EventMonitor.BlockPause:
                        pass
                    else:
                        blockheight += 1
                        if blockheight > blockheight_onchain:
                            need_update = False

                elif 2010 <= block_delta and need_update:
                    # use magic number
                    blockheight = int(blockheight_onchain) - 2000

                    # only update per 15 seconds when the delta is verify large
                    trigger_per_block = True
                    need_update = False

                # update wallet block height
                if need_update or trigger_per_block:
                    EventMonitor.update_wallet_block_height(blockheight)

                # only execute the event machine when the block chain height is updated
                if execute_event_machine:
                    event_machine.handle(blockheight_onchain)
            except Exception as error:
                pass
            finally:
                # check whether the wallet is updated and the event is pooled
                if need_update is False and (event_machine.is_polling_finished or execute_event_machine is False):
                    left_loop_time = end_time - time.time()
                    # suspend this thread until timeout
                    time.sleep(left_loop_time)
                else:
                    # poll per 100 ms
                    time.sleep(0.1)

                # exit this loop for this blockheight
                if end_time - time.time() <= 0.15:  # 150 ms
                    old_blockheight_onchain = blockheight_onchain
                    break
