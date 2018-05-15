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
    
    struct SettleData{
        uint256 closingNonce;             /* transaction nonce that channel closer */
        uint256 expectedSettleBlock;      /* the closing time for final settlement for RSMC */
        uint256 closerSettleBalance;      /* the balance that closer want to withdraw */
    }
    
    struct ChannelData{ 
        mapping(address => uint256) participatorBalance;  /* participator deposted assets*/
        status channelStatus;     /* channel current status  */
        address channelCloser;    /* closer address that closed channel first */
        uint256 channelTotalBalance; /*total balance that both participators deposit together*/
        SettleData settleInfo;    /* settle information*/
    }
    
    struct Data {
        mapping(bytes32 => uint16) channelIndex; 
        mapping(uint16 => ChannelData)channelInfo;
        uint8 channelNumber;
        uint256 settleTimeout;
        address contractOwner;
    }
    
    token public Mytoken;
    Data public trinityData;
    
    /* Define event */
    event Deposit(address partner1, uint256 amount1, address partner2, uint256 amount2, uint16 channelPostion);
    event Settle(address sender, uint256 amount);
    event CloseChannel(address closer, address partner, uint16 channelPostion);
    event DeleteChannel(address partnerA, address partnerB, uint16 channlePosition);
    event Logger(address ecaddress);
    
    
    /* constructor function */
    function TrinityContract(address token_address, uint256 Timeout) public {
        Mytoken=token(token_address);
        trinityData.settleTimeout = Timeout;
        trinityData.channelNumber = 0;
        trinityData.contractOwner = msg.sender;
    }
    
    /* 
     * Function: Set settle timeout value by contract owner only 
    */
    function setSettleTimeout(uint256 blockNumber) public{
        require(msg.sender == trinityData.contractOwner);
        trinityData.settleTimeout = blockNumber;
        return;
    } 

    /* 
     * Function: create a hash value based on two node address that deployed in same channel, the hash will identify the unique channel 
    */
    function createChannelIdentification(address participatorA, address participatorB) internal pure returns(bytes32 channelId){
        return (participatorA <= participatorB) ? (keccak256(participatorA,participatorB)) : (keccak256(participatorB,participatorA));
   }
    
    /*
     * Function: initialize settlement information when setup new channel
     * Parameters:
     *   index: channel position in Data;
     * Return:
         Null
    */
    function initialSettleInfo(uint16 index) internal {
        trinityData.channelInfo[index].settleInfo.closingNonce = 0;
        trinityData.channelInfo[index].settleInfo.expectedSettleBlock = 0;
        trinityData.channelInfo[index].settleInfo.closerSettleBalance = 0;
        
        return;
    }
    /*
     * Function: save channel information
     * Parameters:
     *   participatorA: a paricipator that setup in the same channel;
     *   participatorB: a parnter that setup in the same channel;
     *   amountA : participatorA will lock assets amount;
     *   amountB : participatorB will lock assets amount;
     * Return:
         index: new channel index
    */
    function setupChannel(address participatorA, 
                          address participatorB, 
                          uint256 amountA, 
                          uint256 amountB) internal returns(uint16 channelPostion){
        
        uint16 index;
        bytes32 channelId;
        
        channelId = createChannelIdentification(participatorA, participatorB);
        trinityData.channelNumber += 1;
        index = trinityData.channelNumber;
        trinityData.channelIndex[channelId] = index;
        
        trinityData.channelInfo[index].participatorBalance[participatorA] = amountA;
        trinityData.channelInfo[index].participatorBalance[participatorB] = amountB;
        trinityData.channelInfo[index].channelStatus = status.Opening;
        trinityData.channelInfo[index].channelCloser = address(0);
        trinityData.channelInfo[index].channelTotalBalance = add256(amountA, amountB);
        
        initialSettleInfo(index);
        
        return index;
    }
    
    /*
      * Function: 1. Lock both participants assets to the contract
      *           2. setup channel.
      *           Before lock assets,both participants must approve contract can spend special amout assets.
      * Parameters:
      *    partnerA: partner that deployed on same channel;
      *    partnerB: partner that deployed on same channel;
      *    amountA : partnerA will lock assets amount;
      *    amountB : partnerB will lock assets amount;
      *    signedStringA: partnerA signature for this transaction;
      *    signedStringB: partnerB signature for this transaction;
      * Return:
      *    Null;
    */
    function deposit(address partnerA, 
                     address partnerB,
                     uint256 amountA, 
                     uint256 amountB, 
                     bytes signedStringA, 
                     bytes signedStringB,
                     uint256 depositNonce) public {
        
        uint16 channelPostion = 0;
                         
        //verify both signature to check the behavious is valid.
        require(verifyTransaction(partnerA, partnerB, amountA, amountB, depositNonce, signedStringA, signedStringB) == true);
        
        //transfer both special assets to this contract.
        require(Mytoken.transferFrom(partnerA,this,amountA) == true);
        require(Mytoken.transferFrom(partnerB,this,amountB) == true);
        
        channelPostion = setupChannel(partnerA, partnerB, amountA, amountB);
        emit Deposit(partnerA, amountA, partnerB, amountB, channelPostion);
        
        return;
    }
    
    /*
     * Funcion:   1. set channel status as closing
                  2. withdraw assets for partner against closer 
                  3. freeze closer settle assets untill setelement timeout or partner confirmed the transaction;
     * Parameters:
     *    partnerA: partner that deployed on same channel;
     *    partnerB: partner that deployed on same channel;
     *    settleBalanceA : partnerA will withdraw assets amount;
     *    settleBalanceB : partnerB will withdraw assets amount;
     *    signedStringA: partnerA signature for this transaction;
     *    signedStringB: partnerB signature for this transaction;  
     *    settleNonce: closer provided nonce for settlement;
     * Return:
     *    Null;
    */
    
    function closeChannel(address partnerA, 
                          address partnerB,
                          uint256 settleBalanceA,
                          uint256 settleBalanceB, 
                          bytes signedStringA,
                          bytes signedStringB,
                          uint256 settleNonce) public {
        
        uint16 index = 0;
        bytes32 channelId;
        uint256 settleTotalBalance = 0;
        
        /*verify both signatures to check the behavious is valid*/
        require(verifyTransaction(partnerA, partnerB, settleBalanceA, settleBalanceB, settleNonce, signedStringA, signedStringB) == true);

        channelId = createChannelIdentification(partnerA, partnerB);
        index = trinityData.channelIndex[channelId];
        
        /*sum of both balance should not larger than total deposited assets */
        settleTotalBalance = add256(settleBalanceA, settleBalanceB);
        require(trinityData.channelInfo[index].channelTotalBalance == settleTotalBalance);
        
        /*channel should be opening */
        require(trinityData.channelInfo[index].channelStatus == status.Opening);
        
        trinityData.channelInfo[index].channelStatus = status.Closing;
        trinityData.channelInfo[index].channelCloser = msg.sender;
        trinityData.channelInfo[index].settleInfo.closingNonce = settleNonce;
        if (msg.sender == partnerA){
            /*sender want close channel actively, withdraw partner balance firstly*/
            trinityData.channelInfo[index].settleInfo.closerSettleBalance = settleBalanceA;
            Mytoken.transfer(partnerB, settleBalanceB);
            emit CloseChannel(msg.sender, partnerB, index);
        }
        else
        {
            trinityData.channelInfo[index].settleInfo.closerSettleBalance = settleBalanceB;
            Mytoken.transfer(partnerA, settleBalanceA);
            emit CloseChannel(msg.sender, partnerA, index);
        }
        trinityData.channelInfo[index].settleInfo.expectedSettleBlock = block.number + trinityData.settleTimeout;
                
        return;
    }
    
    /*
     * Function: after apply close channnel, closer can withdraw assets until special settle window period time over
     * Parameters:
     *   partner: partner address that setup in same channel with sender;
     * Return:
         Null
    */
    function settle(address partner) public{

        uint16 index = 0;
        bytes32 channelId;

        channelId = createChannelIdentification(msg.sender, partner);
        index = trinityData.channelIndex[channelId];
        
        /* only chanel closer can call the function and channel status must be closing*/
        require(msg.sender == trinityData.channelInfo[index].channelCloser && trinityData.channelInfo[index].channelStatus == status.Closing);
        require(trinityData.channelInfo[index].settleInfo.expectedSettleBlock <= block.number);

       /* settle period have over and partner didn't provide final transaction information, contract will withdraw closer assets */    
        Mytoken.transfer(msg.sender, trinityData.channelInfo[index].settleInfo.closerSettleBalance);
        
        /* delete channel and cleare channel information*/
        deleteChannel(msg.sender, partner, index, channelId);
        emit Settle(msg.sender, trinityData.channelInfo[index].settleInfo.closerSettleBalance);
        return;
    }
    
    /*
     * Funcion: After closer apply closed channle, partner update owner final transaction to check whether closer submitted invalid information
     *      1. if bothe nonce is same, the submitted settlement is valid, withdraw closer assets
            2. if partner nonce is larger than closer, then jugement closer have submitted invalid data, withdraw closer assets to partner;
            3. if partner nonce is less than closer, then jugement closer submitted data is valid, withdraw close assets.
     * Parameters:
     *    partnerA: partner that deployed on same channel;
     *    partnerB: partner that deployed on same channel;
     *    updateBalanceA : partnerA will withdraw assets amount;
     *    updateBalanceB : partnerB will withdraw assets amount;
     *    signedStringA: partnerA signature for this transaction;
     *    signedStringB: partnerB signature for this transaction;  
     *    settleNonce: closer provided nonce for settlement;
     * Return:
     *    Null;
    */
    
    function updateTransaction(address partnerA, 
                               address partnerB,
                               uint256 updateBalanceA,
                               uint256 updateBalanceB, 
                               bytes signedStringA,
                               bytes signedStringB,
                               uint256 updateNonce) public{
        uint16 index = 0;
        bytes32 channelId;
        
        require(verifyTransaction(partnerA, partnerB, updateBalanceA, updateBalanceB, updateNonce, signedStringA, signedStringB) == true);
        
        channelId = createChannelIdentification(partnerA, partnerB);
        index = trinityData.channelIndex[channelId];        
        
        require(trinityData.channelInfo[index].channelStatus == status.Closing);
        require(trinityData.channelInfo[index].channelCloser != msg.sender);
        
        if (updateNonce <= trinityData.channelInfo[index].settleInfo.closingNonce){
            Mytoken.transfer(trinityData.channelInfo[index].channelCloser, trinityData.channelInfo[index].settleInfo.closerSettleBalance);
        }
        else if (updateNonce > trinityData.channelInfo[index].settleInfo.closingNonce){
            Mytoken.transfer(msg.sender, trinityData.channelInfo[index].settleInfo.closerSettleBalance);
        }
        
        deleteChannel(partnerA, partnerB, index, channelId);
        return;
    }
    
    /*
     * Funcion:   clear channel information
     * Parameters:
     *    partnerA: partner that deployed on same channel;
     *    partnerB: partner that deployed on same channel;
     *    channlePosition: channel index   
     *    channelId: channel identifier;
     * Return:
     *    Null;
    */    
    function deleteChannel(address partnerA, address partnerB, uint16 channlePosition, bytes32 channelId) internal{
        trinityData.channelInfo[channlePosition].channelStatus = status.None;
        trinityData.channelInfo[channlePosition].channelCloser = address(0);
        trinityData.channelInfo[channlePosition].channelTotalBalance = 0;
        trinityData.channelInfo[channlePosition].participatorBalance[partnerA] = 0;
        trinityData.channelInfo[channlePosition].participatorBalance[partnerB] = 0;
        
        trinityData.channelInfo[channlePosition].settleInfo.closingNonce = 0;
        trinityData.channelInfo[channlePosition].settleInfo.expectedSettleBlock = 0;
        trinityData.channelInfo[channlePosition].settleInfo.closerSettleBalance = 0;
        
        trinityData.channelIndex[channelId] = 0;
        
        if (trinityData.channelNumber >= 1){
            trinityData.channelNumber -= 1;
        }
        
        emit DeleteChannel(partnerA, partnerB, channlePosition);
        return;
        
    }  
    
    /*
     * Funcion:   parse both signature for check whether the transaction is valid
     * Parameters:
     *    addressA: node address that deployed on same channel;
     *    addressB: node address that deployed on same channel;
     *    balanceA : nodaA assets amount;
     *    balanceB : nodaB assets assets amount;
     *    nonce: transaction nonce;
     *    signatureA: A signature for this transaction;
     *    signatureB: B signature for this transaction;  
     * Return:
     *    result: if both signature is valid, return TRUE, or return False.
    */  

    function verifyTransaction(
        address addressA,
        address addressB,
        uint256 balanceA,
        uint256 balanceB,
        uint256 nonce,
        bytes signatureA,
        bytes signatureB) internal returns(bool result){
            
        address recoverA;
        address recoverB;
        
        recoverA = recoverAddressFromSignature(addressA, addressB, balanceA ,balanceB, nonce, signatureA);
        recoverB = recoverAddressFromSignature(addressA, addressB, balanceA ,balanceB, nonce, signatureB);
        
        if (recoverA == addressA && recoverB == addressB){
            return true;
        }
        return false;
    }
    
    function recoverAddressFromSignature(
        address addressA,
        address addressB,
        uint256 balanceA,
        uint256 balanceB,
        uint256 nonce,
        bytes signature
        ) internal returns(address)  {

        bytes32 data_hash;
        address recover_addr;
        data_hash=keccak256(addressA,addressB,balanceA,balanceB, nonce);
        recover_addr=_recoverAddressFromSignature(signature,data_hash);
        emit Logger(recover_addr);
        return recover_addr;

    }

	function _recoverAddressFromSignature(bytes signature,bytes32 dataHash) internal returns (address)
    {
        bytes32 r;
        bytes32 s;
        uint8 v;

        (r,s,v)=signatureSplit(signature);

        return ecrecoverDecode(dataHash,v, r, s);
    }

    function signatureSplit(bytes signature)
        pure
        internal
        returns (bytes32 r, bytes32 s, uint8 v)
    {
        assembly {
            r := mload(add(signature, 32))
            s := mload(add(signature, 64))
            v := and(mload(add(signature, 65)), 0xff)
        }
        v=v+27;
        require(v == 27 || v == 28);
    }

    function ecrecoverDecode(bytes32 datahash,uint8 v,bytes32 r,bytes32 s) internal returns(address addr){

        addr=ecrecover(datahash,v,r,s);
        emit Logger(addr);
    }
    
    function add256(uint256 addend, uint256 augend) internal pure returns(uint256 result){
        uint256 sum = addend + augend;
        assert(sum >= addend);
        return sum;
    }
}
