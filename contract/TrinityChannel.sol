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
        address channelSettler;
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
        bool channelExist;
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
    event DepositSuccess(bytes32 channleId, address partnerA, uint256 amountA, address partnerB, uint256 amountB);

    event QuickCloseChannelSuccess(bytes32 channleId, address closer, uint256 amount1, address partner, uint256 amount2);

    event CloseChannelSuccess(bytes32 channleId, address closer, address partner);

    event UpdateTransactionSuccess(bytes32 channleId, address partnerA, uint256 amountA, address partnerB, uint256 amountB);

    event UpdateDepositSuccess(bytes32 channleId, address partnerA, uint256 amountA, address partnerB, uint256 amountB);

    event SettleSuccess(bytes32 channleId, address sender, uint256 amount);


    event WithdrawSuccess(address withdrawer, uint256 amount);

    event Logger(address re_addr);
    // constructor function
    function TrinityContract(address token_address, uint256 Timeout) payable public {
        Mytoken=token(token_address);
        trinityData.settleTimeout = Timeout;
        trinityData.channelNumber = 0;
        trinityData.contractOwner = msg.sender;
    }

    function getChannelCount() external view returns (uint256){
        return trinityData.channelNumber;
    }

    function getChannelById(bytes32 channelId)
             external
             view
             returns(address channelCloser,
                     address channelSettler,
                     address partner1,
                     address partner2,
                     uint256 partner1Balance,
                     uint256 partner2Balance,
                     uint256 channelTotalBalance,
                     uint256 closingNonce,
                     uint256 expectedSettleBlock,
                     uint256 closerSettleBalance,
                     uint256 partnerSettleBalance,
                     status channelStatus){

        ChannelData memory channelInfo = trinityData.channelInfo[channelId];

        channelCloser = channelInfo.channelCloser;
        channelSettler =  channelInfo.channelSettler;
        partner1 = channelInfo.partner1;
        partner2 = channelInfo.partner2;
        partner1Balance = channelInfo.partner1Balance;
        partner2Balance =  channelInfo.partner2Balance;
        channelTotalBalance = channelInfo.channelTotalBalance;
        closingNonce = channelInfo.closingNonce;
        expectedSettleBlock = channelInfo.expectedSettleBlock;
        closerSettleBalance = channelInfo.closerSettleBalance;
        partnerSettleBalance  = channelInfo.partnerSettleBalance;
        channelStatus = channelInfo.channelStatus;
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
    function deposit(bytes32 channelId,
                     uint256 nonce,
                     address funderAddress,
                     uint256 funderAmount,
                     address partnerAddress,
                     uint256 partnerAmount,
                     bytes funderSignature,
                     bytes partnerSignature) payable public {

        //verify both signature to check the behavious is valid.
        if (verifyTransaction(channelId, nonce, funderAddress, funderAmount, partnerAddress, partnerAmount, funderSignature, partnerSignature) == false){
            return;
        }

        /* if channel have existed, can not create it again*/
        if (trinityData.channelInfo[channelId].channelExist == true){
            return;
        }

        trinityData.channelInfo[channelId] = ChannelData(address(0),
                                                         address(0),
                                                         funderAddress,
                                                         partnerAddress,
                                                         funderAmount,
                                                         partnerAmount,
                                                         add256(funderAmount, partnerAmount),
                                                         0,
                                                         0,
                                                         0,
                                                         0,
                                                         status.Opening,
                                                         true);

        //transfer both special assets to this contract.
        if(Mytoken.transferFrom(funderAddress,this,funderAmount) == true){
            if (Mytoken.transferFrom(partnerAddress,this,partnerAmount) == true){
	        trinityData.channelNumber += 1;
                emit DepositSuccess(channelId, funderAddress, funderAmount, partnerAddress, partnerAmount);
                return;
            }
            else{
                Mytoken.transfer(funderAddress, funderAmount);
                delete trinityData.channelInfo[channelId];
                return;
            }
        }

        delete trinityData.channelInfo[channelId];
    }

    function updateDeposit(bytes32 channelId,
                           uint256 nonce,
                           address funderAddress,
                           uint256 funderAmount,
                           address partnerAddress,
                           uint256 partnerAmount,
                           bytes funderSignature,
                           bytes partnerSignature) payable public {

        //verify both signature to check the behavious is valid.
        if (verifyTransaction(channelId, nonce, funderAddress, funderAmount, partnerAddress, partnerAmount, funderSignature, partnerSignature) == false){
            return;
        }

        ChannelData storage channelInfo = trinityData.channelInfo[channelId];

        if (channelInfo.channelStatus != status.Opening){
            return;
        }

        //transfer both special assets to this contract.
        if(Mytoken.transferFrom(funderAddress,this,funderAmount) == true){
            if (Mytoken.transferFrom(partnerAddress,this,partnerAmount) == true){
                if (funderAddress == channelInfo.partner1){
                    channelInfo.partner1Balance += funderAmount;
                    channelInfo.partner2Balance += partnerAmount;
                }
                else if (partnerAddress == channelInfo.partner1){
                    channelInfo.partner1Balance += partnerAmount;
                    channelInfo.partner2Balance += funderAmount;
                }
                channelInfo.channelTotalBalance = add256(channelInfo.partner1Balance, channelInfo.partner2Balance);
                emit UpdateDepositSuccess(channelId, funderAddress, channelInfo.partner1Balance, partnerAddress, channelInfo.partner2Balance);
                return;
            }
            else{
                Mytoken.transfer(funderAddress, funderAmount);
                return;
            }
        }
    }

    function quickCloseChannel(bytes32 channelId,
                               uint256 nonce,
                               address closer,
                               uint256 closerBalance,
                               address partner,
                               uint256 partnerBalance,
                               bytes closerSignature,
                               bytes partnerSignature) payable public{

        uint256 closeTotalBalance = 0;

        //verify both signatures to check the behavious is valid
        if (verifyTransaction(channelId, nonce, closer, closerBalance, partner, partnerBalance, closerSignature, partnerSignature) == false){
            return;
        }

        ChannelData storage channelInfo = trinityData.channelInfo[channelId];

        //channel should be opening
        if (channelInfo.channelStatus != status.Opening){
            return;
        }
        //sum of both balance should not larger than total deposited assets
        closeTotalBalance = add256(closerBalance, partnerBalance);
        if (closeTotalBalance > channelInfo.channelTotalBalance){
            return;
        }
        Mytoken.transfer(closer, closerBalance);
        Mytoken.transfer(partner, partnerBalance);

	    trinityData.channelNumber -= 1;
        delete trinityData.channelInfo[channelId];
        emit QuickCloseChannelSuccess(channelId, closer, closerBalance, partner, partnerBalance);
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

    function closeChannel(bytes32 channelId,
                          uint256 nonce,
                          address partnerA,
                          address partnerB,
                          uint256 closeBalanceA,
                          uint256 closeBalanceB,
                          bytes signedStringA,
                          bytes signedStringB) public {

        uint256 closeTotalBalance = 0;

        //verify both signatures to check the behavious is valid
        if (verifyTransaction(channelId, nonce, partnerA, closeBalanceA, partnerB, closeBalanceB, signedStringA, signedStringB) == false){
            return;
        }

        ChannelData storage channelInfo = trinityData.channelInfo[channelId];

        //channel should be opening
        if (channelInfo.channelStatus != status.Opening){
            return;
        }

        //sum of both balance should not larger than total deposited assets
        closeTotalBalance = add256(closeBalanceA, closeBalanceB);
        if (closeTotalBalance > channelInfo.channelTotalBalance){
            return;
        }

        channelInfo.channelStatus = status.Closing;
        channelInfo.channelCloser = msg.sender;
        channelInfo.closingNonce = nonce;
        if (msg.sender == partnerA){
            //sender want close channel actively, withdraw partner balance firstly
            channelInfo.closerSettleBalance = closeBalanceA;
            channelInfo.partnerSettleBalance = closeBalanceB;
            channelInfo.channelSettler = partnerB;
            emit CloseChannelSuccess(channelId, msg.sender, partnerB);
        }
        else
        {
            channelInfo.closerSettleBalance = closeBalanceB;
            channelInfo.partnerSettleBalance = closeBalanceA;
            channelInfo.channelSettler = partnerA;
            emit CloseChannelSuccess(channelId, msg.sender, partnerA);
        }
        channelInfo.expectedSettleBlock = block.number + trinityData.settleTimeout;
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

    function updateTransaction(bytes32 channelId,
                               uint256 nonce,
                               address partnerA,
                               address partnerB,
                               uint256 updateBalanceA,
                               uint256 updateBalanceB,
                               bytes signedStringA,
                               bytes signedStringB) payable public{

        uint256 updateTotalBalance = 0;

        if (verifyTransaction(channelId, nonce, partnerA, updateBalanceA, partnerB, updateBalanceB, signedStringA, signedStringB) == false){
            return;
        }

        ChannelData storage channelInfo = trinityData.channelInfo[channelId];

        // only when channel status is closing, node can call it
        if (channelInfo.channelStatus != status.Closing){
            return;
        }

        // channel closer can not call it
        if (msg.sender != channelInfo.channelSettler){
            return;
        }

        //sum of both balance should not larger than total deposited assets
        updateTotalBalance = add256(updateBalanceA, updateBalanceB);
        if (updateTotalBalance > channelInfo.channelTotalBalance){
            return;
        }

        channelInfo.channelStatus = status.None;

        // if updated nonce is less than (or equal to) closer provided nonce, folow closer provided balance allocation
        if (nonce <= channelInfo.closingNonce){
            Mytoken.transfer(channelInfo.channelCloser, channelInfo.closerSettleBalance);
            Mytoken.transfer(channelInfo.channelSettler, channelInfo.partnerSettleBalance);
            emit UpdateTransactionSuccess(channelId,
                                          channelInfo.channelCloser,
                                          channelInfo.closerSettleBalance,
                                          channelInfo.channelSettler,
                                          channelInfo.partnerSettleBalance);
        }

        // if updated nonce is equal to nonce+1 that closer provided nonce, folow partner provided balance allocation
        else if (nonce == (channelInfo.closingNonce + 1)){
            Mytoken.transfer(partnerA, updateBalanceA);
            Mytoken.transfer(partnerB, updateBalanceB);
            emit UpdateTransactionSuccess(channelId, partnerA, updateBalanceA, partnerB, updateBalanceB);
        }

        // if updated nonce is larger than nonce+1 that closer provided nonce, determine closer provided invalid transaction, partner will also get closer assets
        else if (nonce > (channelInfo.closingNonce + 1)){
            Mytoken.transfer(channelInfo.channelSettler, updateTotalBalance);
            emit UpdateTransactionSuccess(channelId, channelInfo.channelSettler, updateTotalBalance, channelInfo.channelCloser, 0);
        }
        trinityData.channelNumber -= 1;
        delete trinityData.channelInfo[channelId];
        return;
    }

    /*
     * Function: after apply close channnel, closer can withdraw assets until special settle window period time over
     * Parameters:
     *   partner: partner address that setup in same channel with sender;
     * Return:
         Null
    */

    function settleTransaction(bytes32 channelId) payable public{

        ChannelData storage channelInfo = trinityData.channelInfo[channelId];

        // only chanel closer can call the function and channel status must be closing
        if (msg.sender != channelInfo.channelCloser){
            return;
        }
        if (channelInfo.channelStatus != status.Closing){
            return;
        }
        if (channelInfo.expectedSettleBlock > block.number){
            return;
        }

        channelInfo.channelStatus = status.None;

       // settle period have over and partner didn't provide final transaction information, contract will withdraw closer assets
        Mytoken.transfer(channelInfo.channelCloser, channelInfo.closerSettleBalance);
        Mytoken.transfer(channelInfo.channelSettler, channelInfo.partnerSettleBalance);

        // delete channel
	    trinityData.channelNumber -= 1;
        delete trinityData.channelInfo[channelId];
        emit SettleSuccess(channelId, msg.sender, channelInfo.closerSettleBalance);
        return;
    }

    function withdraw(address partner,
                      //bytes locked_encoded,
                      uint64 expiration,
                      uint256 amount,
                      bytes32 timeLockHash,
                      bytes32 secret,
                      bytes partnerSigned) public{

        //uint64 expiration;
        //uint256 amount;
        //bytes32 timeLockHash;
        bytes32 channelId;

        //(expiration, amount,timeLockHash) = decodeLock(locked_encoded);

        if (partner != verifyTimelock(partner, msg.sender, expiration, amount, timeLockHash,partnerSigned)){
            return;
        }

        if (timeLockHash != keccak256(secret)){
            return;
        }

        if (block.number < expiration){
            return;
        }

        channelId = createChannelIdentification(msg.sender, partner);
        ChannelData storage channelInfo = trinityData.channelInfo[channelId];

        if (partner == channelInfo.partner1){
            channelInfo.partner1Balance = sub256(channelInfo.partner1Balance, amount);
        }
        else if(partner == channelInfo.partner2){
            channelInfo.partner2Balance = sub256(channelInfo.partner2Balance, amount);
        }
        channelInfo.channelTotalBalance = add256(channelInfo.partner1Balance,  channelInfo.partner2Balance);
        Mytoken.transfer(msg.sender, amount);
        emit WithdrawSuccess(msg.sender, amount);
    }

    /*
     * Function: create a hash value based on two node address that deployed in same channel, the hash will identify the unique channel
    */

    function createChannelIdentification(address participatorA, address participatorB) internal pure returns(bytes32 channelId){
        return (participatorA < participatorB) ? (keccak256(participatorA,participatorB)) : (keccak256(participatorB,participatorA));
    }

    function verifyTimelock(
        address sender,
        address receiver,
        uint64 expiration,
        uint256 amount,
        bytes32 timeLockHash,
        bytes signature
        ) internal pure returns(address)  {

        bytes32 data_hash;
        address recover_addr;
        data_hash=keccak256(sender,receiver,expiration, amount,timeLockHash);
        recover_addr=_recoverAddressFromSignature(signature,data_hash);
        return recover_addr;
    }

    function decodeLock(bytes lock)
        pure
        internal
        returns (uint64 expiration, uint amount, bytes32 hashlock)
    {
        require(lock.length == 72);

        // Lock format:
        // [0:8] expiration
        // [8:40] amount
        // [40:72] hashlock
        assembly {
            expiration := mload(add(lock, 8))
            amount := mload(add(lock, 40))
            hashlock := mload(add(lock, 72))
        }
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
        bytes32 channelId,
        uint256 nonce,
        address addressA,
        uint256 balanceA,
        address addressB,
        uint256 balanceB,
        bytes signatureA,
        bytes signatureB) internal  returns(bool result){

        address recoverA;
        address recoverB;

        recoverA = recoverAddressFromSignature(channelId, nonce, addressA, balanceA, addressB, balanceB, signatureA);
        recoverB = recoverAddressFromSignature(channelId, nonce, addressA, balanceA, addressB, balanceB, signatureB);
        if (recoverA == addressA && recoverB == addressB){
            return true;
        }
        return false;
    }

    function recoverAddressFromSignature(
        bytes32 channelId,
        uint256 nonce,
        address addressA,
        uint256 balanceA,
        address addressB,
        uint256 balanceB,
        bytes signature
        ) internal pure returns(address)  {

        bytes32 data_hash;
        address recover_addr;
        data_hash=keccak256(channelId, nonce, addressA, balanceA, addressB, balanceB);
        recover_addr=_recoverAddressFromSignature(signature,data_hash);
        return recover_addr;

    }

	function _recoverAddressFromSignature(bytes signature,bytes32 dataHash) internal pure returns (address)
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

    function ecrecoverDecode(bytes32 datahash,uint8 v,bytes32 r,bytes32 s) internal pure returns(address addr){

        addr=ecrecover(datahash,v,r,s);
        return addr;
    }

    function add256(uint256 addend, uint256 augend) internal pure returns(uint256 result){
        uint256 sum = addend + augend;
        assert(sum >= addend);
        return sum;
    }

    function sub256(uint256 a, uint256 b) internal pure returns (uint256) {
        assert(b <= a);
        return a - b;
    }
}