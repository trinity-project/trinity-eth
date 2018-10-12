# Trinity
Trinity is a universal off-chain scaling solution, which aims to achieve real-time payments with low transaction fees, scalability and privacy protection for mainchain assets. Using state channel technology, Trinity will significantly increase the transaction throughput of underlying chains as well as the assets on smart contracts. TNC cross-chain converter facilitates the data and value flow between multiple chains. Trinity will be a fully autonomous and decentralized performance-enhancing network for the entire ecosystem and provides all-round support to Dapps on bottom layer chains in the future.
https://trinity.tech
# Trinity-eth
trinity-eth is the implementation of trinity protocol based on ethereum.

# Trinity-ETH Network Configuration Guide
>Note: Trinity node deployment process requires the configuration environment be python 3.6 and above versions. 
As the Trinity project continues to evolve, this file may not apply to the Trinity network released in the future; this file was tested on Ubuntu 16.04.
## Trinity Runtime Environment Preparation
>Description: Trinity is developed based on Python 3.6. A very useful tool with python is virtualenv, which is used to build an isolated virtual python environment for the project. It is key to maintain a clean environment during configuration. This file recommends using vitraulenv to keep you in the process of building a node. Details of virtualenv can be found at: https://virtualenv.pypa.io/ En/stable/. Another package management tool with python is Pip, which helps developer easily installed and manage the project. For more information on Pip, please refer to: https://pip.pypa.io/en/stable/

>Trinity uses mongodb as local data base. Mongodb is a well-known open source no-sql database. It has high performance, easy to deploy and use for data storage. For more information about mongodb, please refer to: https ://www.mongodb.com/

>The Trinity node needs to specify a public IP that can be reached in the external communication and the ports you use in the next configuration. Please make sure that the firewall does not block the ports. If you use a cloud server, please refer to your service provider document. If you use a local server, please contact your network service provider for more details. 

>This file uses Screen as terminals. For more info on Screen, please visit: http://man7.org/linux/man-pages/man1/screen.1.html 

### Install the Dependency Tools
Install system libraries and system tools

```
sudo apt-get install screen git libleveldb-dev libssl-dev g++
```
Install mongodb and launch the service

```
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 2930ADAE8CAF5059EE73BB4B58712A2291FA4AD5

echo "deb [ arch=amd64,arm64 ] http://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/3.6 multiverse" | sudo tee /etc/apt/sourcves.list.d/mongodb-org-3.6.list

sudo apt-get update

sudo apt-get install mongodb-org

sudo service mongod start
```
*Ref: Mongodb configuration details, please visit https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/*

Install python3.6

```
sudo apt-get install software-properties-common

sudo add-apt-repository ppa:jonathonf/python-3.6

sudo apt-get update

sudo apt-get install python3.6 python3.6-dev
```

Install pip 3.6

```
sudo wget https://bootstrap.pypa.io/get-pip.py

sudo python3.6 get-pip.py

```
Install virtualenv

```
sudo pip3.6 install virtualenv
```
## Get Trinity Source Code

```
git clone https://github.com/trinity-project/trinity-eth.git <your dictionary> ##get wallet code
git clone https://github.com/trinity-project/trinity-gateway.git <your dictionary> ##get gateway code
```
Enter the trinity-eth directory

```
cd <your dictionary>/trinity-eth
```
Create and activate a virtual environment

```
virtualenv -p /usr/bin/python3.6 venv

source venv/bin/activate
```
Install the trinity node dependency package

```
pip install -r requirements
```
Enter the wallet directory

```
cd <your dictionary>/trinity-eth
```
Create and activate a virtual environment

```
virtualenv -p /usr/bin/python3.6 venv

source venv/bin/activate
```
Install the trinity node dependency package

```
pip install -r requirements
```

## Install Trinity Routing Node Gateway 

Open gateway configuration file

```
vi gateway/config.py
```
*Find* cg_public_ip_port = "localhost:8189" *in the localhost and set it as user’s public ip address.*
*Eg: cg_public_ip_port = "8.8.8.8:8189"*

Create a new session window

```
screen -S TrinityGateway #TrinityGateway: users can change this name
```
Enter virtual environment

```
source venv/bin/activate
```

Run the Gateway service

```
python start.py
```

The message below on the console indicates the Gateway successfully started. 

```
###### Trinity Gateway Start Successfully! ######
```
Use ctrl+a+d to detach the current TrinityGateway session window.

*Note: Call the function below to reopen the existing TrinityGateway session window*

```
screen -r TrinityGateway
```
## Install Trinity Routing Node Wallet

Modify configuration file

```
cd <your dictionary>/trinity-eth/wallet
```
*The default configuration file applies to the testnet. Both configure_testnet.py and configure_mainnet.py exist in the wallet directory. When deploying on the mainnet, users can simply copy configure_mainnet.py into configure.py. Please refer to notes for configuration details.*

Create a new session window

```
screen -S TrinityWallet #TrinityWallet: users can change this name
```
Activate python3.6 virtualenv (find it in venv directory)

```
source venv/bin/activate
``` 

Run the Wallet Services (find it in trinity/wallet directory)  

+ Mainnet Wallet

```
python3.6 prompt.py -m #mainnet wallet

```
+ Testnet Wallet

```
python3.6 prompt.py #testnet wallet
```

*To detach or resume the wallet session, please refer to the section of running gateways.*

## Channel Nodes Interworking

After the running of Trinity CLI wallet, the subsequent wallet and channel operations can be performed on the console.
Input ‘help’ to the wallet console to view all trinity CLI wallet commands. 
Here are a few channel-related commands: 

1. Use create wallet command to set up an address before using the channel.

```
trinity> create wallet <your wallet file name> 
```

2. Open the existing wallet.

*Note: The wallet to be opened should have state-channel functions, otherwise the function will be limited.*

```
trinity> open wallet <your wallet file name>
```

*Note: after creating or re-opening a wallet, the wallet will automatically connect to the gateway and enable channel function. If channel function was not enabled within 30s, please call channel function to open it manually.*

3. Use channel enable command to enable channel function before operating on state channels.

```
trinity> channel enable 
```

4. View the wallet uir through channel show uri command

```
trinity> channel show uri
```

5. Create channel

```
trinity> channel create xxxxxxxxxxxxx@xx.xx.xx.xx:xxxx TNC 80000 # create parameters：peer node uri(PublicKey@ip_address:port）, asset_type, deposit
```

*Note: TNC deposit is calculated on 800 USD, which means 800 TNC is required if TNC current price is $ 1 USD. The command below will tell how much TNC is needed currently for deposit. This is only valid for TNC channel.*

6. Call channel depoist_limit to check the minimum TNC deposit

```
trinity> channel deposit_limit
```

7. Call channel tx to execute off-chain transactions. Use paymentlink code, or uri + asset + value as tx parameters.
 
```
trinity> channel tx xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx # payment link 
```

Or

```
trinity> channel tx xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx@xx.xx.xx.xx:xxxx TNC 10
```

8. Call channel payment to generate payment code

```
trinity> channel payment TNC 10 "mytest" # payment parameters: asset type， value，comments， comments can be empty
```

9. Call channel close to complete settlement and close the channel

```
trinity> channel close xxxxxxxxxxxxxxx #close parameters: channel name
```

10. Call channel peer to check peer nodes in the current channel

```
trinity> channel peer
```
