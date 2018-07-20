pragma solidity ^0.4.23;

contract MyVerifySig {
    event Logger(address ecaddress);


    function recoverAddressFromSignature(
        address addressA,
        address addressB,
        uint256 balanceA,
        uint256 balanceB,
        bytes signature
        ) public returns(address)  {

        bytes32 data_hash;
        address recover_addr;
        data_hash=keccak256(addressA,addressB,balanceA,balanceB);
        recover_addr=_recoverAddressFromSignature(signature,data_hash);
        Logger(recover_addr);
        return recover_addr;

    }


	function _recoverAddressFromSignature(bytes signature,bytes32 dataHash) public  returns (address)
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



    function ecrecoverDecode(bytes32 datahash,uint8 v,bytes32 r,bytes32 s) internal   returns(address addr){

        addr=ecrecover(datahash,v,r,s);
        emit Logger(addr);
    }


}