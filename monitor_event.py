import json
import time
import redis
from web3 import Web3, HTTPProvider



# pool= redis.ConnectionPool(host="localhost",port=6379,decode_responses=True)
pool= redis.ConnectionPool(host="47.104.81.20",port=9001,decode_responses=True)
redis_client=redis.Redis(connection_pool=pool)

event_set=set()
has_pushed=[]

TOPICS_OF_ERC_TRANSFER="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ADDRESS_OF_ERC721_WOB="0x5296aAF564a7a15DE46840AA2b9742C205b0A70E"
ADDRESS_OF_ERC20_TNC="0x65096f2b7a8dc1592479f1911cd2b98dae4d2218"



def push_event(to_push_message):
    while True:
        try:
            redis_client.publish("monitor", to_push_message)
            return True
        except Exception as e:
            print("connect redis fail lead to push fail:{}".format(to_push_message))
            time.sleep(3)



def handle_logs(logs):

    tmp_dict={}
    for item in logs:
        # print(item)
        if item.get("address") ==ADDRESS_OF_ERC721_WOB:
            if item.get("topics")[0].hex()==TOPICS_OF_ERC_TRANSFER:

                tmp_dict["txId"]=item.get("transactionHash").hex()
                tmp_dict["eventType"]="transfer"
                tmp_dict["addressFrom"]="0x"+item.get("data")[26:66]
                tmp_dict["addressTo"]="0x"+item.get("data")[90:130]
                tmp_dict["messageType"]="monitorEthTransfer"
                tmp_dict["tokenId"]=int("0x"+item.get("data")[130:194],16)

                to_push_event=json.dumps(tmp_dict)
                if to_push_event not in has_pushed:

                    result=push_event(to_push_event)
                    if result:
                        has_pushed.append(to_push_event)




def get_logs(web3):
    event_logs = web3.eth.getLogs({
        "fromBlock": "latest",
        "address": [ADDRESS_OF_ERC721_WOB],
        "topics": [TOPICS_OF_ERC_TRANSFER]
    })

    return event_logs

def log_loop(web3, poll_interval=0):
    while True:
        event_logs = get_logs(web3)
        handle_logs(event_logs)
        time.sleep(poll_interval)

        # break




def main():
    # w3 = Web3(HTTPProvider('http://192.168.214.178:8545'))
    # w3 = Web3(HTTPProvider('https://mainnet.infura.io/pZc5ZTRYM8wYfRPtoQal'))
    w3 = Web3(HTTPProvider('https://ropsten.infura.io/pZc5ZTRYM8wYfRPtoQal'))
    log_loop(w3)

if __name__ == '__main__':
    main()