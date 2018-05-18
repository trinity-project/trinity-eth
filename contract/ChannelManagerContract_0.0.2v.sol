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
    
    struct ChannelData{ 
        address channelCloser;    /* closer address that closed channel first */
        address partner1;
        address partner2;
        uint256 partner1Balance;
        uint256 partner2Balance;
        uint256 channelTotalBalance; /*total balance that both participators deposit together*/
        uint256 closingNonce;             /* transaction nonce that channel closer */
        uint256 expectedSettleBlock;      /* the closing time for final settlement for RSMC */
        uint256 closerSettleBalance;      /* the balance that closer want to withdraw */
        uint256 partnerSettleBalance;     /* the balance that closer provided for partner can withdraw */
        status channelStatus;             /* channel current status  */
    }
    
    struct Data {
        mapping(bytes32 => ChannelData)channelInfo; 
        uint8 channelNumber;
        uint256 settleTimeout;
        address contractOwner;
    }
    
    token public Mytoken;
    Data public trinityData;
    
    /* Define event */
    event DepositSuccess(address partnerA, uint256 amountA, address partnerB, uint256 amountB, bytes32 channleId);
    event DepositFailure(address partnerA, address partnerB);
    
    event QuickCloseChannelSuccess(address closer, uint256 amount1, address partner, uint256 amount2, bytes32 channleId);
    event QuickCloseChannelFailure(address closer, address partner, uint256 totalBalance);
    
    event CloseChannelSuccess(address closer, address partner, bytes32 channleId);
    event CloseChannelFailure(address closer, address partner, uint256 totalBalance);
    
    event UpdateTransactionSuccess(address partnerA, uint256 amountA, address partnerB, uint256 amountB, bytes32 channleId);
    event UpdateTransactionFailure(address partnerA, address partnerB, uint256 totalBalance);
    
    event UpdateDepositSuccess(address partnerA, uint256 amountA, address partnerB, uint256 amountB);
    event UpdateDepositFailure(address partnerA, address partnerB);
    
    event SettleSuccess(address sender, uint256 amount, bytes32 channleId);
    event SettleFailure(address sender, uint256 blockNumber);
    
    event DeleteChannel(address partnerA, address partnerB, bytes32 channleId);
    
    event Logger(address ecaddress);
    
    // constructor function
    function TrinityContract(address token_address, uint256 Timeout) payable public {
        Mytoken=token(token_address);
        trinityData.settleTimeout = Timeout;
        trinityData.channelNumber = 0;
        trinityData.contractOwner = msg.sender;
    }
    
    function setupChannel(address participatorA, 
                          address participatorB, 
                          uint256 amountA, 
                          uint256 amountB, 
                          bytes32 channelId) internal {
        
        trinityData.channelInfo[channelId].partner1Balance = amountA;
        trinityData.channelInfo[channelId].partner2Balance = amountB;
        trinityData.channelInfo[channelId].channelTotalBalance = add256(amountA, amountB); 
        trinityData.channelInfo[channelId].partner1 = participatorA;
        trinityData.channelInfo[channelId].partner2 = participatorB;
        trinityData.channelInfo[channelId].channelStatus = status.Opening;
        trinityData.channelInfo[channelId].channelCloser = address(0);
        trinityData.channelInfo[channelId].closingNonce = 0;
        trinityData.channelInfo[channelId].expectedSettleBlock = 0;
        trinityData.channelInfo[channelId].closerSettleBalance = 0;
        trinityData.channelInfo[channelId].partnerSettleBalance = 0;

        trinityData.channelNumber += 1;
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
                     uint256 depositNonce) payable public {
        
        bytes32 channelId;
                         
        //verify both signature to check the behavious is valid.
        if (verifyTransaction(partnerA, partnerB, amountA, amountB, depositNonce, signedStringA, signedStringB) == false){
            emit DepositFailure(address(0), address(0));
            return;
        }
        
        channelId = createChannelIdentification(partnerA, partnerB);
        /* if channel with expected channlId have existed, can not create it again*/
        if (trinityData.channelInfo[channelId].channelStatus == status.Opening || trinityData.channelInfo[channelId].channelStatus == status.Closing){
            emit DepositFailure(partnerA, partnerB);
            return;
        }
        
        //transfer both special assets to this contract.
        if(Mytoken.transferFrom(partnerA,this,amountA) == true){
            if (Mytoken.transferFrom(partnerB,this,amountB) == true){
                setupChannel(partnerA, partnerB, amountA, amountB, channelId);
                emit DepositSuccess(partnerA, amountA, partnerB, amountB, channelId);
                return;
            }
            else{
                Mytoken.transfer(partnerA, amountA);
                emit DepositFailure(partnerB, 0);
                return;
            }
        }
        emit DepositFailure(partnerA, 0);
    }    
    
    function updateDeposit(address partnerA, 
                           address partnerB,
                           uint256 amountA, 
                           uint256 amountB, 
                           bytes signedStringA, 
                           bytes signedStringB,
                           uint256 depositNonce) payable public {
        bytes32 channelId;
                               
        //verify both signature to check the behavious is valid.
        if (verifyTransaction(partnerA, partnerB, amountA, amountB, depositNonce, signedStringA, signedStringB) == false){
            emit UpdateDepositFailure(address(0), address(0));
            return;
        }
        
        channelId = createChannelIdentification(partnerA, partnerB);
 
        if (trinityData.channelInfo[channelId].channelStatus != status.Opening){
            emit UpdateDepositFailure(partnerA, partnerB);
            return;
        }
    
        //transfer both special assets to this contract.
        if(Mytoken.transferFrom(partnerA,this,amountA) == true){
            if (Mytoken.transferFrom(partnerB,this,amountB) == true){
                if (partnerA == trinityData.channelInfo[channelId].partner1){
                    trinityData.channelInfo[channelId].partner1Balance += amountA;
                    trinityData.channelInfo[channelId].partner2Balance += amountB;
                }
                else if (partnerB == trinityData.channelInfo[channelId].partner1){
                    trinityData.channelInfo[channelId].partner1Balance += amountB;
                    trinityData.channelInfo[channelId].partner2Balance += amountA;
                }
                trinityData.channelInfo[channelId].channelTotalBalance = add256(trinityData.channelInfo[channelId].partner1Balance, trinityData.channelInfo[channelId].partner2Balance);
                emit UpdateDepositSuccess(partnerA, trinityData.channelInfo[channelId].partner1Balance, partnerB, trinityData.channelInfo[channelId].partner2Balance);
                return;
            }
            else{
                Mytoken.transfer(partnerA, amountA);
                emit UpdateDepositFailure(partnerB, 0);
                return;
            }
        }
        emit UpdateDepositFailure(partnerA, 0);
    }    
    
    function quickCloseChannel(address partnerA, 
                               address partnerB,
                               uint256 closeBalanceA,
                               uint256 closeBalanceB, 
                               bytes signedStringA,
                               bytes signedStringB,
                               uint256 closeNonce,
                               bool isQuickCloseChannel) payable public{
        
        uint256 closeTotalBalance = 0;
        bytes32 channelId;
        
        channelId = createChannelIdentification(partnerA, partnerB);
        
        //verify both signatures to check the behavious is valid
        if (verifyTransaction(partnerA, partnerB, closeBalanceA, closeBalanceB, closeNonce, signedStringA, signedStringB) == false){
            emit QuickCloseChannelFailure(address(0), address(0), 0);
            return;
        }
        
        require(isQuickCloseChannel == true);
        
        //channel should be opening 
        if (trinityData.channelInfo[channelId].channelStatus != status.Opening){
            emit QuickCloseChannelFailure(partnerA, partnerB, 0);
            return;
        }
        //sum of both balance should not larger than total deposited assets 
        closeTotalBalance = add256(closeBalanceA, closeBalanceB);
        if (closeTotalBalance > trinityData.channelInfo[channelId].channelTotalBalance){
            emit QuickCloseChannelFailure(partnerA, partnerB, closeTotalBalance);
            return;
        }
        Mytoken.transfer(partnerA, closeBalanceA);
        Mytoken.transfer(partnerB, closeBalanceB);
        
        deleteChannel(partnerA, partnerB, channelId);
        emit QuickCloseChannelSuccess(partnerA, closeBalanceA, partnerB, closeBalanceB,  channelId);
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
                          uint256 closeBalanceA,
                          uint256 closeBalanceB, 
                          bytes signedStringA,
                          bytes signedStringB,
                          uint256 closeNonce) public {

        bytes32 channelId;
        uint256 closeTotalBalance = 0;
        
        //verify both signatures to check the behavious is valid
        if (verifyTransaction(partnerA, partnerB, closeBalanceA, closeBalanceB, closeNonce, signedStringA, signedStringB) == false){
            emit CloseChannelFailure(address(0), address(0), 0);
            return;
        }

        channelId = createChannelIdentification(partnerA, partnerB);
        
        //channel should be opening 
        if (trinityData.channelInfo[channelId].channelStatus != status.Opening){
            emit CloseChannelFailure(partnerA, partnerB, 0);
            return;
        }
        
        //sum of both balance should not larger than total deposited assets
        closeTotalBalance = add256(closeBalanceA, closeBalanceB);
        if (closeTotalBalance > trinityData.channelInfo[channelId].channelTotalBalance){
            emit CloseChannelFailure(partnerA, partnerB, closeTotalBalance);
            return;
        }
        
        trinityData.channelInfo[channelId].channelStatus = status.Closing;
        trinityData.channelInfo[channelId].channelCloser = msg.sender;
        trinityData.channelInfo[channelId].closingNonce = closeNonce;
        if (msg.sender == partnerA){
            //sender want close channel actively, withdraw partner balance firstly
            trinityData.channelInfo[channelId].closerSettleBalance = closeBalanceA;
            trinityData.channelInfo[channelId].partnerSettleBalance = closeBalanceB;
            emit CloseChannelSuccess(msg.sender, partnerB, channelId);
        }
        else
        {
            trinityData.channelInfo[channelId].closerSettleBalance = closeBalanceB;
            trinityData.channelInfo[channelId].partnerSettleBalance = closeBalanceA;
            emit CloseChannelSuccess(msg.sender, partnerA, channelId);
        }
        trinityData.channelInfo[channelId].expectedSettleBlock = block.number + trinityData.settleTimeout;
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
                               uint256 updateNonce) payable public{
        bytes32 channelId;
        uint256 updateTotalBalance = 0;
        
        if (verifyTransaction(partnerA, partnerB, updateBalanceA, updateBalanceB, updateNonce, signedStringA, signedStringB) == false){
            emit UpdateTransactionFailure(address(0), address(0), 0);
            return;
        }
        
        channelId = createChannelIdentification(partnerA, partnerB);
        
        // only when channel status is closing, node can call it
        if (trinityData.channelInfo[channelId].channelStatus != status.Closing){
            emit UpdateTransactionFailure(partnerA, partnerB, 0);
            return;
        }
        
        // channel closer can not call it 
        if (trinityData.channelInfo[channelId].channelCloser == msg.sender){
            emit UpdateTransactionFailure(trinityData.channelInfo[channelId].channelCloser , msg.sender, 0);
            return;    
        }
        
        //sum of both balance should not larger than total deposited assets 
        updateTotalBalance = add256(updateBalanceA, updateBalanceB);
        if (updateTotalBalance > trinityData.channelInfo[channelId].channelTotalBalance){
            emit UpdateTransactionFailure(partnerA, partnerB, updateTotalBalance);
            return;
        } 
        
        trinityData.channelInfo[channelId].channelStatus = status.None;
        
        // if updated nonce is less than (or equal to) closer provided nonce, folow closer provided balance allocation
        if (updateNonce <= trinityData.channelInfo[channelId].closingNonce){
            Mytoken.transfer(trinityData.channelInfo[channelId].channelCloser, trinityData.channelInfo[channelId].closerSettleBalance);
            Mytoken.transfer(msg.sender, trinityData.channelInfo[channelId].partnerSettleBalance);
            emit UpdateTransactionSuccess(trinityData.channelInfo[channelId].channelCloser, 
                                          trinityData.channelInfo[channelId].closerSettleBalance,
                                          msg.sender,
                                          trinityData.channelInfo[channelId].partnerSettleBalance,
                                          channelId);
        }
        
        // if updated nonce is equal to nonce+1 that closer provided nonce, folow partner provided balance allocation
        else if (updateNonce == (trinityData.channelInfo[channelId].closingNonce + 1)){
            Mytoken.transfer(partnerA, updateBalanceA);
            Mytoken.transfer(partnerB, updateBalanceB);
            emit UpdateTransactionSuccess(partnerA, updateBalanceA, partnerB, updateBalanceB, channelId);
        }
        
        // if updated nonce is larger than nonce+1 that closer provided nonce, determine closer provided invalid transaction, partner will also get closer assets
        else if (updateNonce > (trinityData.channelInfo[channelId].closingNonce + 1)){
            Mytoken.transfer(msg.sender, updateTotalBalance);
            emit UpdateTransactionSuccess(msg.sender, updateTotalBalance, trinityData.channelInfo[channelId].channelCloser, 0, channelId);
        }
        
        deleteChannel(partnerA, partnerB, channelId);
        return;
    }  

    /*
     * Function: after apply close channnel, closer can withdraw assets until special settle window period time over
     * Parameters:
     *   partner: partner address that setup in same channel with sender;
     * Return:
         Null
    */
    
    function settle(address partner) payable public{

        bytes32 channelId;

        channelId = createChannelIdentification(msg.sender, partner);
        
        // only chanel closer can call the function and channel status must be closing
        if (msg.sender != trinityData.channelInfo[channelId].channelCloser){
            emit SettleFailure(msg.sender, 0);
            return;
        }
        if (trinityData.channelInfo[channelId].channelStatus != status.Closing){
            emit SettleFailure(partner, 0);
            return;
        }
        if (trinityData.channelInfo[channelId].expectedSettleBlock > block.number){
            emit SettleFailure(msg.sender, trinityData.channelInfo[channelId].expectedSettleBlock);
            return;
        }
        
        trinityData.channelInfo[channelId].channelStatus = status.None;

       // settle period have over and partner didn't provide final transaction information, contract will withdraw closer assets   
        Mytoken.transfer(msg.sender, trinityData.channelInfo[channelId].closerSettleBalance);
        Mytoken.transfer(partner, trinityData.channelInfo[channelId].partnerSettleBalance);
        
        // delete channel and cleare channel information
        deleteChannel(msg.sender, partner, channelId);
        emit SettleSuccess(msg.sender, trinityData.channelInfo[channelId].closerSettleBalance, channelId);
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
    function deleteChannel(address partnerA, address partnerB, bytes32 channelId) internal {
        trinityData.channelInfo[channelId].channelStatus = status.None;
        trinityData.channelInfo[channelId].channelCloser = address(0);
        trinityData.channelInfo[channelId].channelTotalBalance = 0;
        trinityData.channelInfo[channelId].partner1 = address(0);
        trinityData.channelInfo[channelId].partner2 = address(0);
        trinityData.channelInfo[channelId].partner1Balance = 0;
        trinityData.channelInfo[channelId].partner2Balance = 0;
        
        trinityData.channelInfo[channelId].closingNonce = 0;
        trinityData.channelInfo[channelId].expectedSettleBlock = 0;
        trinityData.channelInfo[channelId].closerSettleBalance = 0;
        trinityData.channelInfo[channelId].partnerSettleBalance = 0;
        
        if (trinityData.channelNumber >= 1){
            trinityData.channelNumber -= 1;
        }
        emit DeleteChannel(partnerA, partnerB, channelId);
    }  
    
    /* 
     * Function: create a hash value based on two node address that deployed in same channel, the hash will identify the unique channel 
    */
    
    function createChannelIdentification(address participatorA, address participatorB) internal pure returns(bytes32 channelId){
        return (participatorA < participatorB) ? (keccak256(participatorA,participatorB)) : (keccak256(participatorB,participatorA));
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
