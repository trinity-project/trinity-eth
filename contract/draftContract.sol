pragma solidity ^0.4.18;

interface token {
    function transferFrom (address _from,address _to, uint256 _value) external returns (bool success);
    function approve (address _spender,uint256 _value) external;
    function transfer(address _to, uint256 _value) external; 
}

contract TrinityContract{
    /*
     *  Define public data interface
     *  Mytoken: ERC20 standard token contract address
     *  trinityData: story channel status and balance, support multiple channel;
    */
    enum status {None, Opening, Closing}
    
    struct SettleInfo{
        uint256 closingNonce;             /* transaction nonce that channel closer */
        uint256 expectedSettleBlock;      /* the closing time for final settlement for RSMC */
        uint256 expectedSettleBalance;    /* the balance that closer provided */
        bool waintingSettle;              /* judement whether closer provided invalid transaction informaiton for HTLC*/
    }
    
    struct ChannelInfo
    {
        status channelStatus;             /* channel current status  */
        //uint256 channelIdentifier;       
        bool isChannelCloser;             /* judement whether the participator closed channel first */     
        address closerAddress;            /* closer address that closed channel first */
        mapping(address => uint256)lockedBalance;  /* participator deposted assets*/
        mapping(address => SettleInfo)settleData;  /* store closer provided settle information*/
    }
    
    struct Data {
        mapping(address => mapping(address =>uint8)) channelIndex; 
        mapping(uint256 => ChannelInfo)channelData;
        uint8 channelNumber;
        uint256 lockBlockNumber;
        address owner;
    }
    
    token public Mytoken;
    Data public trinityData;
    
    /* Define event */
    event Depoist(address sender, uint256 amount);
    event Settle(address sender, uint256 amount);
    
    
    /* constructor function */
    function TrinityContract(address token_address, uint256 blockNumber) public {
        Mytoken=token(token_address);
        trinityData.lockBlockNumber = blockNumber;
        trinityData.channelNumber = 0;
        trinityData.owner = msg.sender;
    }
    
    /* 
     * Function: Set settle timeout value by contract owner only 
    */
    function setSettleTimeout(uint256 blockNumber) public{
        require(msg.sender == trinityData.owner);
        trinityData.lockBlockNumber = blockNumber;
        return;
    } 
    
    /*
     * Function: initialize channel information when setup new channel 
    */
    function initialChanel(address participator1, address participator2) internal {
        ChannelInfo storage channelInfo = trinityData.channelData[trinityData.channelIndex[participator1][participator2]];
        channelInfo.isChannelCloser = false;
        channelInfo.closerAddress = address(0);
        channelInfo.settleData[participator1].closingNonce = 0;
        channelInfo.settleData[participator1].expectedSettleBlock = 0;
        channelInfo.settleData[participator1].expectedSettleBalance = 0;
        channelInfo.settleData[participator1].waintingSettle = true;
        return;
    }
    /*
     * Function: save channel information
     * Parameters:
     *   participator1: participator that setup in the channel;
     *   participator2: partner that setup in the channel;
     *   amount: locked assets amount;
    */
    function setupChannel(address participator1, address participator2, uint256 amount) internal{
        
        uint8 channelIndex;
        
        trinityData.channelIndex[participator1][participator2] += 1;
        channelIndex = trinityData.channelIndex[participator1][participator2];
        trinityData.channelData[channelIndex].channelStatus = status.Opening;
        trinityData.channelData[channelIndex].lockedBalance[participator1] = amount;
        
        initialChanel(participator1, participator2);
        
        trinityData.channelNumber += 1;
        
        return;
    }
    
    /*
      * Function: 1. Lock participants assets to the contract
      *          2. Save related information to channel.
      *          Before lock assets,participants must approve contract to spend special amout assets.
      * Parameters:
      *    partner: partner that deployed on same channel with sender.
      *    amount:  locked assets amount;
    */
    function depoist(address partner,uint256 amount) public {
        require(Mytoken.transferFrom(msg.sender,this,amount) == true);
        setupChannel(msg.sender, partner, amount);
        emit Depoist(msg.sender, amount);
        
        return;
    }
    
    /*
     * Funcion: close channel 
    */
    
    function closeChannel(address partner, uint256 senderBalace, uint256 partnerBalance, uint256 nonce) public {
        // sender must has deposted assets to channel
        ChannelInfo storage senderChannelInfo = trinityData.channelData[trinityData.channelIndex[msg.sender][partner]];
        ChannelInfo storage partnerChannelInfo = trinityData.channelData[trinityData.channelIndex[partner][msg.sender]];
        
        uint256 totalBalance = add(senderChannelInfo.lockedBalance[msg.sender], partnerChannelInfo.lockedBalance[partner]);
        
        require(senderChannelInfo.channelStatus == status.Opening);
        require((senderBalace + partnerBalance) <= totalBalance);
        
        // if parter didn't deposit assets to channel, contract will withdraw assets at channel directly.
        if (partnerChannelInfo.channelStatus == status.None){
            require(senderBalace <= senderChannelInfo.lockedBalance[msg.sender]);
            Mytoken.transfer(msg.sender, senderBalace);
            emit Settle(msg.sender, senderBalace);
            clearChannel(msg.sender, partner);
            return;
        }
        
        // if partner has deposited assets and channel is Opening
        if (partnerChannelInfo.channelStatus == status.Opening){
            
            senderChannelInfo.isChannelCloser = true;
            
            senderChannelInfo.channelStatus = status.Closing;
            senderChannelInfo.closerAddress = msg.sender;
            
            senderChannelInfo.settleData[msg.sender].closingNonce = nonce;
            
            if (verifyBalance())
            {
                /*Sender want close channel actively, withdraw partner balance firstly*/
                Mytoken.transfer(partner, partnerBalance);
                emit Settle(partner, partnerBalance);
                
                /* waiting for special time for partner verify whether both balance is valid  */
                senderChannelInfo.settleData[msg.sender].expectedSettleBlock = block.number + trinityData.lockBlockNumber;
                senderChannelInfo.settleData[msg.sender].expectedSettleBalance = senderBalace;
                
                settle(partner);
                return;
            }
        }
        
        /* if partner has deposited assets and channel is closing*/
        if (partnerChannelInfo.channelStatus == status.Closing){
            return;
        }
    }
    
    function settle(address partner) haveTimeover(partner) public{
        ChannelInfo storage senderChannelInfo = trinityData.channelData[trinityData.channelIndex[msg.sender][partner]];

        if (msg.sender == senderChannelInfo.closerAddress && senderChannelInfo.channelStatus == status.Closing)
        {
            if (senderChannelInfo.settleData[msg.sender].waintingSettle == false){
                return;
            }
            
            Mytoken.transfer(msg.sender, senderChannelInfo.settleData[msg.sender].expectedSettleBalance);
            clearChannel(msg.sender, partner);
            emit Settle(msg.sender, senderChannelInfo.settleData[msg.sender].expectedSettleBalance);
            return;
        }
        return;
    }
    
    function updateTransction(address partner, uint256 updatedNonce) public{
        require(verifyBalance() == true);
        
        ChannelInfo storage senderChannelInfo = trinityData.channelData[trinityData.channelIndex[msg.sender][partner]];
        ChannelInfo storage partnerChannelInfo = trinityData.channelData[trinityData.channelIndex[partner][msg.sender]];        
        require(senderChannelInfo.channelStatus == status.Opening);
        require(partnerChannelInfo.channelStatus == status.Closing);
        require(partnerChannelInfo.isChannelCloser == true && partnerChannelInfo.closerAddress == partner);
        
        uint256 settleNonce = partnerChannelInfo.settleData[partner].closingNonce;
        if (updatedNonce > settleNonce){
            partnerChannelInfo.settleData[partner].waintingSettle = false;
            Mytoken.transfer(msg.sender, partnerChannelInfo.settleData[partner].expectedSettleBalance);
            clearChannel(msg.sender, partner);
            return;
        }
        if (updatedNonce <= settleNonce){
            return;
        }
    }
    
    function verifyBalance() internal pure returns(bool result){
        return true;
    }
    
    function add(uint256 value1, uint256 value2) internal pure returns(uint256 result){
        uint256 sum = value1 + value2;
        assert(sum >= value1);
        return sum;
    }
    
    modifier haveTimeover(address partner) {
        ChannelInfo storage senderChannelInfo = trinityData.channelData[trinityData.channelIndex[msg.sender][partner]];
        require(senderChannelInfo.settleData[msg.sender].expectedSettleBlock <= block.number);
        _;
    }
    
    function clearChannel(address sender, address parter) internal{
        ChannelInfo storage channelInfo = trinityData.channelData[trinityData.channelIndex[sender][parter]];
        channelInfo.channelStatus = status.None;
        //channelInfo.channelIdentifier;
        //channelInfo.channelCloser = false;
        channelInfo.closerAddress = address(0);
        channelInfo.isChannelCloser = false;
        channelInfo.lockedBalance[sender] = 0;
        channelInfo.settleData[sender].expectedSettleBlock = 0;
        channelInfo.settleData[sender].expectedSettleBalance = 0;
        channelInfo.settleData[sender].closingNonce = 0;
        
        if (trinityData.channelNumber >= 1){
            trinityData.channelNumber -= 1;
        }
        return;
    }
}
