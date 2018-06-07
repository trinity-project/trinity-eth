pragma solidity ^0.4.18;

interface token {
    function transferFrom (address _from,address _to, uint256 _value) external returns (bool success);
}

contract BatchTransfer{
    token Mytoken;
    address  owner;
    
    function BatchTransfer() public{
        owner=msg.sender;
    }
    
    function setTokenAddress(address contract_address) public {
        require (msg.sender==owner);
        Mytoken=token(contract_address);
    }
 
    function sendTransaction(address[] accounts, uint256[] amounts, address addressFrom) public{
        require(msg.sender==addressFrom);
        require(accounts.length == amounts.length);
        
        address transferAccount = 0x0;
        uint256 transferAmount = 0;
        uint256 transferNumber = 0;
        
        transferNumber = accounts.length;
        
        for(uint8 i=0; i< transferNumber; i++){
            transferAccount = accounts[i];
            transferAmount = amounts[i];
            Mytoken.transferFrom(addressFrom,transferAccount, transferAmount);
         }
    }
}