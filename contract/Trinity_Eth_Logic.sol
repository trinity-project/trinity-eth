pragma solidity ^0.4.18;

interface token {
    function transferFrom (address _from,address _to, uint256 _value) external returns (bool success);
}

interface trinityData{
    
    function getChannelBalance(bytes32 channelId) external view returns (uint256);
    function getChannelStatus(bytes32 channelId) external view returns(uint8);
    function getChannelExist(bytes32 channelId) external view returns(bool);
    function getChannelClosingSettler(bytes32 channelId) external view returns (address);
    
    function getClosingSettle(bytes32 channelId)external view returns (uint256,uint256,address,address,uint256,uint256);
    function getTimeLock(bytes32 channelId, bytes32 lockHash) external view returns(address,address,uint256,uint256, uint256, bool);
}

contract TrinityEvent{

    event Deposit(bytes32 channleId, address partnerA, uint256 amountA,address partnerB, uint256 amountB);
    event UpdateDeposit(bytes32 channleId, address partnerA, uint256 amountA, address partnerB, uint256 amountB);    
    event QuickCloseChannel(bytes32 channleId, address closer, uint256 amount1, address partner, uint256 amount2);
    event CloseChannel(bytes32 channleId, address closer, address partner);
    event UpdateTransaction(bytes32 channleId, address partnerA, uint256 amountA, address partnerB, uint256 amountB);
    event Settle(bytes32 channleId, address partnerA, uint256 amountA, address partnerB, uint256 amountB);
    event Withdraw(bytes32 channleId, bytes32 hashLock);
    event WithdrawUpdate(bytes32 channleId, bytes32 hashLock, uint256 balance);
    event WithdrawSettle(bytes32 channleId, bytes32 hashLock, uint256 balance);   
    event SetSettleTimeout(uint256 timeoutBlock);
}

contract Owner{
    address public owner;
    bool paused;
    
    constructor() public{
        owner = msg.sender;
        paused = false;
    }
    
    modifier onlyOwner(){
        require(owner == msg.sender);
        _;
    } 
    
    modifier whenNotPaused(){
        require(!paused);
        _;
    }

    modifier whenPaused(){
        require(paused);
        _;
    }

    //disable contract setting funciton
    function pause() external onlyOwner whenNotPaused {
        paused = true;
    }

    //enable contract setting funciton
    function unpause() public onlyOwner whenPaused {
        paused = false;
    }    
}

contract VerifySignature{
    
    function verifyTimelock(bytes32 channelId,
                            uint256 nonce,
                            address sender,
                            address receiver,
                            uint256 lockPeriod ,
                            uint256 lockAmount,
                            bytes32 lockHash,
                            bytes partnerAsignature,
                            bytes partnerBsignature) internal pure returns(bool)  {

        address recoverA = verifyLockSignature(channelId, nonce, sender, receiver, lockPeriod, lockAmount,lockHash, partnerAsignature);
        address recoverB = verifyLockSignature(channelId, nonce, sender, receiver, lockPeriod, lockAmount,lockHash, partnerBsignature);
        if ((recoverA == sender && recoverB == receiver) || (recoverA == receiver && recoverB == sender)){
            return true;
        }
        return false;
    }

    function verifyLockSignature(bytes32 channelId,
                                uint256 nonce,
                                address sender,
                                address receiver,
                                uint256 lockPeriod ,
                                uint256 lockAmount,
                                bytes32 lockHash,
                                bytes signature) internal pure returns(address)  {

        bytes32 data_hash;
        address recover_addr;
        data_hash=keccak256(channelId, nonce, sender, receiver, lockPeriod, lockAmount,lockHash);
        recover_addr=_recoverAddressFromSignature(signature,data_hash);
        return recover_addr;
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
        bytes signatureB) internal pure returns(bool result){

        address recoverA;
        address recoverB;

        recoverA = recoverAddressFromSignature(channelId, nonce, addressA, balanceA, addressB, balanceB, signatureA);
        recoverB = recoverAddressFromSignature(channelId, nonce, addressA, balanceA, addressB, balanceB, signatureB);
        if ((recoverA == addressA && recoverB == addressB) || (recoverA == addressB && recoverB == addressA)){
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
        require((v == 27 || v == 28), "check v value");
    }

    function ecrecoverDecode(bytes32 datahash,uint8 v,bytes32 r,bytes32 s) internal pure returns(address addr){

        addr=ecrecover(datahash,v,r,s);
        return addr;
    }
}

library SafeMath{
    
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

contract TrinityContractCore is Owner, VerifySignature, TrinityEvent{

    using SafeMath for uint256;

    uint8 constant OPENING = 1;
    uint8 constant CLOSING = 2;
    uint8 constant LOCKING = 3;
    

    trinityData public trinityDataContract;
    token public Mytoken;
    string public debugInfo;
    
    constructor(address _tokenAddress, address _dataAddress) public{
        Mytoken = token(_tokenAddress);
        trinityDataContract = trinityData(_dataAddress);
    }
    
    function getChannelBalance(bytes32 channelId) public view returns (uint256){
        return trinityDataContract.getChannelBalance(channelId);
    }   

   function getChannelStatus(bytes32 channelId) public view returns (uint8){
        return trinityDataContract.getChannelStatus(channelId);
    }

    function setDataContract(address _dataContract) external onlyOwner {
        trinityDataContract = trinityData(_dataContract);
    }
    
    /*
     * Function: Set asset token address by contract owner only
    */
    function setToken(address tokenAddress) external onlyOwner{
        Mytoken=token(tokenAddress);
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
                     bytes partnerSignature) external whenNotPaused{

        //verify both signature to check the behavious is valid.
        
        require(verifyTransaction(channelId, 
                                  nonce, 
                                  funderAddress, 
                                  funderAmount, 
                                  partnerAddress, 
                                  partnerAmount, 
                                  funderSignature, 
                                  partnerSignature) == true);
        
        bool channelExist = trinityDataContract.getChannelExist(channelId);
        //if channel have existed, can not create it again
        require(channelExist == false, "check whether channel exist");
        
        require(Mytoken.transferFrom(funderAddress,trinityDataContract,funderAmount) == true, "deposit from funder");
        require(Mytoken.transferFrom(partnerAddress,trinityDataContract,partnerAmount) == true, "deposit from partner");        
        
        bool callResult = address(trinityDataContract).call(bytes4(keccak256("createChannel(bytes32,address,uint256,address,uint256)")),
                                                channelId,
                                                funderAddress,
                                                funderAmount,
                                                partnerAddress,
                                                partnerAmount);
                                                
        require(callResult == true);
        
        emit Deposit(channelId, funderAddress, funderAmount, partnerAddress, partnerAmount);
    }

    function updateDeposit(bytes32 channelId,
                           uint256 nonce,
                           address funderAddress,
                           uint256 funderAmount,
                           address partnerAddress,
                           uint256 partnerAmount,
                           bytes funderSignature,
                           bytes partnerSignature) external whenNotPaused{
        
        //verify both signature to check the behavious is valid.
        require(verifyTransaction(channelId, nonce, funderAddress, funderAmount, partnerAddress, partnerAmount, funderSignature, partnerSignature) == true, "verify signature");
        
        require(getChannelStatus(channelId) == OPENING, "check channel status");

        require(Mytoken.transferFrom(funderAddress,trinityDataContract,funderAmount) == true, "deposit from funder");
        require(Mytoken.transferFrom(partnerAddress,trinityDataContract,partnerAmount) == true, "deposit from partner");

        bool callResult = address(trinityDataContract).call(bytes4(keccak256("updateDeposit(bytes32,uint256,uint256)")),
                                                channelId,
                                                funderAmount,
                                                partnerAmount);

        require(callResult == true, "call result");
        
        emit UpdateDeposit(channelId, funderAddress, funderAmount, partnerAddress, partnerAmount);
    }

    function quickCloseChannel(bytes32 channelId,
                               uint256 nonce,
                               address funder,
                               uint256 funderBalance,
                               address partner,
                               uint256 partnerBalance,
                               bytes closerSignature,
                               bytes partnerSignature) external whenNotPaused{

        uint256 closeTotalBalance = 0;
 
        //verify both signatures to check the behavious is valid
        require(verifyTransaction(channelId, nonce, funder, funderBalance, partner, partnerBalance, closerSignature, partnerSignature) == true, "verify signature");

        require(nonce == 0, "check nonce");

        require((msg.sender == funder || msg.sender == partner), "verify caller");

        //channel should be opening
        require(getChannelStatus(channelId) == OPENING, "check channel status");
        
        //sum of both balance should not larger than total deposited assets
        closeTotalBalance = funderBalance.add256(partnerBalance);
        require(closeTotalBalance == getChannelBalance(channelId),"check channel balance");
 
        bool callResult = address(trinityDataContract).call(bytes4(keccak256("quickCloseChannel(bytes32,address,uint256,address,uint256)")),
                                                channelId,
                                                funder,
                                                funderBalance,
                                                partner,
                                                partnerBalance);

        require(callResult == true, "call result");
        
        
        emit QuickCloseChannel(channelId, funder, funderBalance, partner, partnerBalance);
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
                          address founder,
                          uint256 founderBalance,      
                          address partner,
                          uint256 partnerBalance,
                          bytes closerSignature,
                          bytes partnerSignature) public whenNotPaused{

        bool callResult;
        uint256 closeTotalBalance = 0;

        //verify both signatures to check the behavious is valid
        require(verifyTransaction(channelId, nonce, founder, founderBalance, partner, partnerBalance, closerSignature, partnerSignature) == true, "verify signature");

        require(nonce != 0, "check nonce");

        require((msg.sender == founder || msg.sender == partner), "check caller");

        //channel should be opening
        require(getChannelStatus(channelId) == OPENING, "check channel status");

        //sum of both balance should not larger than total deposited assets
        closeTotalBalance = founderBalance.add256(partnerBalance);
        require(closeTotalBalance == getChannelBalance(channelId), "check total balance");

        if (msg.sender == founder){
            //sender want close channel actively, withdraw partner balance firstly
            callResult = address(trinityDataContract).call(bytes4(keccak256("closeChannel(bytes32,uint256,address,uint256,address,uint256)")),
                                                channelId,
                                                nonce,
                                                founder,
                                                founderBalance,
                                                partner,
                                                partnerBalance);

            require(callResult == true);    
        }
        else if(msg.sender == partner)
        {
            callResult = address(trinityDataContract).call(bytes4(keccak256("closeChannel(bytes32,uint256,address,uint256,address,uint256)")),
                                                channelId,
                                                nonce,
                                                partner,
                                                partnerBalance,
                                                founder,
                                                founderBalance);

            require(callResult == true);              
        }
        
        emit CloseChannel(channelId, founder, partner);
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
    uint256 gclosingNonce;
    uint256 gcloserBalance;
    uint256 gsettlerBalance;
    uint256 gchannelTotalBalance;
    
    function updateTransaction(bytes32 channelId,
                               uint256 nonce,
                               address partnerA,
                               uint256 updateBalanceA,       
                               address partnerB,
                               uint256 updateBalanceB,
                               bytes signedStringA,
                               bytes signedStringB) external whenNotPaused{

        address channelCloser;
        address channelSettler;
        uint256 updateTotalBalance = 0;
        
        require(verifyTransaction(channelId, nonce, partnerA, updateBalanceA, partnerB, updateBalanceB, signedStringA, signedStringB) == true, "verify signature");

        require(nonce != 0, "check nonce");

        require((msg.sender == partnerA || msg.sender == partnerB), "check caller");

        // only when channel status is closing, node can call it
        require(getChannelStatus(channelId) == CLOSING, "check channel status");

        // channel closer can not call it
        require(msg.sender == trinityDataContract.getChannelClosingSettler(channelId), "check settler");

        //sum of both balance should not larger than total deposited asset
        updateTotalBalance = updateBalanceA.add256(updateBalanceB);
        gchannelTotalBalance = getChannelBalance(channelId);
        require(updateTotalBalance == gchannelTotalBalance, "check total balance");
        
        (gclosingNonce, ,channelCloser,channelSettler,gcloserBalance,gsettlerBalance) = trinityDataContract.getClosingSettle(channelId);
        // if updated nonce is less than (or equal to) closer provided nonce, folow closer provided balance allocation
        if (nonce <= gclosingNonce){
            
        }

        // if updated nonce is equal to nonce+1 that closer provided nonce, folow partner provided balance allocation
        else if (nonce == (gclosingNonce + 1)){
            channelCloser = partnerA;
            gcloserBalance = updateBalanceA;
            channelSettler = partnerB;
            gsettlerBalance = updateBalanceB;
        }

        // if updated nonce is larger than nonce+1 that closer provided nonce, determine closer provided invalid transaction, partner will also get closer assets
        else if (nonce > (gclosingNonce + 1)){
            gcloserBalance = 0;
            gsettlerBalance = gchannelTotalBalance;
        }        
        
        bool callResult = address(trinityDataContract).call(bytes4(keccak256("closingSettle(bytes32,address,uint256,address,uint256)")),
                                                channelId,
                                                channelCloser,
                                                gcloserBalance,
                                                channelSettler,
                                                gsettlerBalance);

        require(callResult == true);
        
        emit UpdateTransaction(channelId, channelCloser, gcloserBalance, channelSettler, gsettlerBalance);
        
        gsettlerBalance = 0;
        gcloserBalance = 0;
        gclosingNonce = 0;
        gchannelTotalBalance = 0;
}
    
    /*
     * Function: after apply close channnel, closer can withdraw assets until special settle window period time over
     * Parameters:
     *   partner: partner address that setup in same channel with sender;
     * Return:
         Null
    */
 
    function settleTransaction(bytes32 channelId) external whenNotPaused{
    
        uint256 expectedSettleBlock;
        uint256 closerBalance;
        uint256 settlerBalance;
        address channelCloser;
        address channelSettler;
    
        (, expectedSettleBlock,channelCloser,channelSettler,closerBalance,settlerBalance) = trinityDataContract.getClosingSettle(channelId); 
        
        // only chanel closer can call the function and channel status must be closing
        require(msg.sender == channelCloser, "check closer");
        
        require(expectedSettleBlock < block.number, "check settle time");        
        
        require(getChannelStatus(channelId) == CLOSING, "check channel status");
        
        bool callResult = address(trinityDataContract).call(bytes4(keccak256("closingSettle(bytes32,address,uint256,address,uint256)")),
                                                channelId,
                                                channelCloser,
                                                closerBalance,
                                                channelSettler,
                                                settlerBalance);

        require(callResult == true);        
        
        emit Settle(channelId, channelCloser, closerBalance, channelSettler, settlerBalance);
    }
    
    address gwithdrawer;
    address gwithdrawVerifier;
    uint256 gupdateNonce;
    bool gwithdrawLocked;

    function withdraw(bytes32 channelId,
                      uint256 nonce,
                      address sender,
                      address receiver,
                      uint256 lockTime ,
                      uint256 lockAmount,
                      bytes32 lockHash,
                      bytes partnerAsignature,
                      bytes partnerBsignature,
                      bytes32 secret) external {

        require(verifyTimelock(channelId, nonce, sender, receiver, lockTime,lockAmount,lockHash,partnerAsignature,partnerBsignature) == true, "verify signature");

        require(nonce != 0, "check nonce");

        (, , gupdateNonce, , ,gwithdrawLocked) = trinityDataContract.getTimeLock(channelId,lockHash);
        require(nonce >= gupdateNonce, "check nonce");
        
        require(lockTime > block.number, "check lock time");        

        require(lockHash == keccak256(secret), "verify hash");
        
        require(msg.sender == receiver, "check caller");
        
        require(lockAmount <= getChannelBalance(channelId));

        require(gwithdrawLocked == false, "check withdraw status");

        bool callResult = address(trinityDataContract).call(bytes4(keccak256("withdrawLocks(bytes32,uint256,uint256,uint256,bytes32)")),
                                                channelId,
                                                nonce,
                                                lockAmount,
                                                lockTime,
                                                lockHash);  
                                                
        bool result = address(trinityDataContract).call(bytes4(keccak256("withdrawPartners(bytes32,address,address,bytes32)")),
                                                channelId,
                                                sender,
                                                receiver,
                                                lockHash);                                                 
                                                
        require(callResult == true && result == true);
        
        emit Withdraw(channelId, lockHash);
        
        gupdateNonce = 0;
        gwithdrawLocked = false;
    }

    function withdrawUpdate(bytes32 channelId,
                      uint256 nonce,
                      address sender,
                      address receiver,
                      uint256 lockTime ,
                      uint256 lockAmount,
                      bytes partnerAsignature,
                      bytes partnerBsignature,
                      bytes32 lockHash) external whenNotPaused{


        bool callResult;
        bool withdrawLocked;
        
        require(verifyTimelock(channelId, nonce, sender, receiver, lockTime,lockAmount,lockHash,partnerAsignature,partnerBsignature) == true, "verify signature");

        require(nonce != 0, "check nonce");

        require(lockTime > block.number, "check lock time"); 

        (gwithdrawVerifier,gwithdrawer,gupdateNonce, , ,withdrawLocked) = trinityDataContract.getTimeLock(channelId,lockHash);
        
        require(withdrawLocked == true, "check withdraw status");
        
        require(msg.sender == gwithdrawVerifier, "check verifier");
        
        gchannelTotalBalance = getChannelBalance(channelId);
        require(lockAmount <= gchannelTotalBalance);
        
        if (nonce <= gupdateNonce){
            gchannelTotalBalance = gchannelTotalBalance.sub256(lockAmount);
            
            callResult = address(trinityDataContract).call(bytes4(keccak256("withdrawSettle(bytes32,address,uint256,uint256,bytes32)")),
                                                channelId,
                                                gwithdrawer,
                                                lockAmount,
                                                gchannelTotalBalance,
                                                lockHash);            
        }
        else if(nonce > gupdateNonce){

            callResult = address(trinityDataContract).call(bytes4(keccak256("withdrawSettle(bytes32,address,uint256,uint256,bytes32)")),
                                                channelId,
                                                gwithdrawVerifier,
                                                gchannelTotalBalance,
                                                0,
                                                lockHash);   
            gchannelTotalBalance = 0;                                    
        }    

        require(callResult == true);        
        
        emit WithdrawUpdate(channelId, lockHash, gchannelTotalBalance);
        
        gwithdrawVerifier = address(0);
        gwithdrawer = address(0);
        gchannelTotalBalance = 0;
        gupdateNonce = 0;
    }

    function withdrawSettle(bytes32 channelId,
                            bytes32 lockHash,
                            bytes32 secret) external whenNotPaused{
                                
        address _withdrawer;
        uint256 lockAmount;
        uint256 lockTime;
        uint256 _channelTotalBalance;
        bool withdrawLocked;
        
        require(lockHash == keccak256(secret), "verify hash");
        
        (,_withdrawer, ,lockAmount,lockTime,withdrawLocked) = trinityDataContract.getTimeLock(channelId,lockHash);
        
        require(withdrawLocked == true, "check withdraw status");
        
        require(msg.sender == _withdrawer, "check caller");
        
        require(lockTime < block.number, "check time lock");           

        _channelTotalBalance = getChannelBalance(channelId);
        _channelTotalBalance = _channelTotalBalance.sub256(lockAmount);

        bool callResult = address(trinityDataContract).call(bytes4(keccak256("withdrawSettle(bytes32,address,uint256,uint256,bytes32)")),
                                                channelId,
                                                msg.sender,
                                                lockAmount,
                                                _channelTotalBalance,
                                                lockHash);   
                                                
        require(callResult == true);   
        
        emit WithdrawSettle(channelId, lockHash, _channelTotalBalance);
    }

    function () public { revert(); }
}