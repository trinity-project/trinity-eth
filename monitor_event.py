import asyncio
from web3 import Web3, HTTPProvider

w3 = Web3(HTTPProvider('http://192.168.214.178:8545'))


def handle_event(event):
    print(event)
    # and whatever

async def log_loop(event_filter, poll_interval):
    while True:
        for event in event_filter.get_new_entries():
            handle_event(event)
        await asyncio.sleep(poll_interval)

def main():
    block_filter = w3.eth.filter({"address":"0x445E08fCE1E43606f8D39B14E372eA084B75C5f1"})
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            asyncio.gather(
                log_loop(block_filter, 2)))
    finally:
        loop.close()

if __name__ == '__main__':
    main()