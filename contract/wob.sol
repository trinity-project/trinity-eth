pragma solidity ^0.4.18;

contract ERC721 {
    // Required methods
    function totalSupply() public view returns (uint256 total);
    function balanceOf(address _owner) public view returns (uint256 balance);
    function ownerOf(uint256 _tokenId) public view returns (address owner);
    function approve(address _to, uint256 _tokenId) external;
    function transfer(address _to, uint256 _tokenId) external;
    function transferFrom(address _from, address _to, uint256 _tokenId) external;

    // Events
    event Transfer(address from, address to, uint256 tokenId);
    event Approval(address owner, address approved, uint256 tokenId);
}

/* enable and disable contract function*/
contract AccessControl {

    address public WOBOwner;
    bool public paused = false;

    modifier onlyCLevel() {
        require(msg.sender == WOBOwner);
        _;
    }

    function setCEO(address _newOwner) external onlyCLevel {
        require(_newOwner != address(0));
        WOBOwner = _newOwner;
    }

    modifier whenNotPaused(){
        require(!paused);
        _;
    }

    modifier whenPaused(){
        require(paused);
        _;
    }

    /*disable contract setting funciton*/
    function pause() external onlyCLevel whenNotPaused {
        paused = true;
    }

    /*enable contract setting funciton*/
    function unpause() public onlyCLevel whenPaused {
        paused = false;
    }
}

/*implement base ERC721 function */
contract NFTbase is ERC721{
    /*** EVENTS ***/
    event Create(address owner, uint256 tokenId);

    /*** STORAGE ***/

    /*token attribute*/
    struct NFTtoken {
        string attribute;
        uint256 birthTime;
    }

    address public WOBOwner;

    mapping (uint256 => address) internal tokenOwner;       //the owner corresponding to each token
    mapping (address => uint256) internal ownedTokensCount; //the owner that owned total token number
    mapping (uint256 => address) internal tokenApprovals;
    mapping (uint256 => bool) internal isNFTAlive;          //check whether the life value of NFT is valid

    function _transfer(address _from, address _to, uint256 _tokenId) internal {
        ownedTokensCount[_to]++;
        tokenOwner[_tokenId] = _to;
        if (_from != address(0)) {
            ownedTokensCount[_from]--;
            delete tokenApprovals[_tokenId];
        }

        emit Transfer(_from, _to, _tokenId);
    }

    function _blink(uint256 _tokenId, address _owner) internal{

        require(tokenOwner[_tokenId] == address(0));
        _transfer(0, _owner, _tokenId);

        emit Create(_owner,_tokenId);
    }

    function _burn(address _from, uint256 _tokenId) internal {

        require(_owns(_from, _tokenId));

        ownedTokensCount[_from]--;
        tokenOwner[_tokenId] = address(0);
        delete tokenApprovals[_tokenId];
    }

    function _owns(address _tokenOwner, uint256 _tokenId) internal view returns (bool){
        return tokenOwner[_tokenId] == _tokenOwner;
    }

    function ownerOf(uint256 _tokenId)public view returns (address owner)
    {
        owner = tokenOwner[_tokenId];
        require(owner != address(0));
    }

    function balanceOf(address _owner) public view returns (uint256 count) {
        return ownedTokensCount[_owner];
    }

    function _approvedFor(address _claimant, uint256 _tokenId) internal view returns (bool) {
        return tokenApprovals[_tokenId] == _claimant;
    }

    function _approve(uint256 _tokenId, address _approved) internal {
        tokenApprovals[_tokenId] = _approved;
    }
}

contract NFTcontrol is NFTbase, AccessControl{

    NFTtoken[] allNFTtokens;
    mapping (uint256 => uint256) internal tokdenIdToNFTindex;

    uint256[] allTokens;
    mapping(uint256 => uint256) internal allTokensIndex;

    mapping (address => uint256[]) internal ownedTokens;
    mapping (uint256 => uint256) internal ownedTokensIndex;

    string public constant name = "W0BT";
    string public constant symbol = "WOB";


    function transfer(address _to, uint256 _tokenId) external whenNotPaused{

        require(_to != address(0));
        require(_to != address(this));
        require(_owns(msg.sender, _tokenId));

        removeTokenFromOwnship(msg.sender, _tokenId);
        addTokenTo(_to, _tokenId);

        _transfer(msg.sender, _to, _tokenId);
    }

    function approve(address _to, uint256 _tokenId) external whenNotPaused{

        require(_to != address(0));
        require(_owns(msg.sender, _tokenId));

        _approve(_tokenId, _to);

        emit Approval(msg.sender, _to, _tokenId);
    }

    function transferFrom(address _from, address _to, uint256 _tokenId) external whenNotPaused{

        require(_to != address(0));
        require(_to != address(this));
        require(_approvedFor(msg.sender, _tokenId) || msg.sender == _from);
        require(_owns(_from, _tokenId));

        removeTokenFromOwnship(_from, _tokenId);
        addTokenTo(_to, _tokenId);

        _transfer(_from, _to, _tokenId);
    }

    function totalSupply() public view returns (uint256) {
        return allTokens.length-1;
    }

    function tokensOfOwner(address _owner) external view returns(uint256[]) {
        return ownedTokens[_owner];
    }

    function getAllTokens() external view returns(uint256[]){
        return allTokens;
    }

    function addTokenTo(address _to, uint256 _tokenId) internal{
        ownedTokens[_to].push(_tokenId);
        ownedTokensIndex[_tokenId] = ownedTokens[_to].length -1 ;
    }

    /*create new NFT asset*/
    function createNFT(uint256[] _idArray, address _owner) public whenNotPaused onlyCLevel{

        uint256 _tokenId;

        for (uint8 tokenNum=0; tokenNum < _idArray.length; tokenNum++){

            _tokenId = _idArray[tokenNum];

            super._blink(_tokenId, _owner);

            NFTtoken memory _NFTtoken = NFTtoken({
                attribute: "",
                birthTime: uint64(now)
            });

            isNFTAlive[_tokenId] = true;
            if (_owner == address(0)){
                isNFTAlive[_tokenId] = false;
                _NFTtoken.birthTime = 0;
            }

            allNFTtokens.push(_NFTtoken);
            tokdenIdToNFTindex[_tokenId] = allNFTtokens.length - 1;

            allTokens.push(_tokenId);
            allTokensIndex[_tokenId] = allTokens.length - 1;

            addTokenTo(_owner, _tokenId);
        }
    }

    function removeTokenFromOwnship(address _from, uint256 _tokenId) internal {

        uint256 tokenIndex = ownedTokensIndex[_tokenId];
        uint256 lastTokenIndex = ownedTokens[_from].length - 1;
        uint256 lastToken = ownedTokens[_from][lastTokenIndex];

        ownedTokens[_from][tokenIndex] = lastToken;
        ownedTokens[_from][lastTokenIndex] = uint256(0);

        ownedTokens[_from].length--;
        ownedTokensIndex[_tokenId] = 0;
        ownedTokensIndex[lastToken] = tokenIndex;
    }
}

contract WOBCore is NFTcontrol{

    event SetNFTbyTokenId(uint256 tokenId, bool result);

    function WOBCore() payable public{
        WOBOwner = msg.sender;
        uint256[] memory initialNFTid = new uint256[](1);
        initialNFTid[0] == 0;

        createNFT(initialNFTid, address(0));
    }

    function getNFTbyTokenId(uint256 _tokenId) external view returns(string attribute, uint256 birthTime, bool status){

        uint256 _tokenIndex = tokdenIdToNFTindex[_tokenId];
        require(_tokenIndex != 0);

        NFTtoken memory _NFTtoken = allNFTtokens[_tokenIndex];

        attribute = _NFTtoken.attribute;
        birthTime = _NFTtoken.birthTime;
        status = isNFTAlive[_tokenId];
    }

    function setNFTbyTokenId(uint256 _tokenId, string attribute, bool status)external whenNotPaused onlyCLevel{

        require(isNFTAlive[_tokenId] == true);
        uint256 _tokenIndex = tokdenIdToNFTindex[_tokenId];
        require(_tokenIndex != 0);

        NFTtoken storage _NFTtoken = allNFTtokens[_tokenIndex];

        _NFTtoken.attribute = attribute;
        isNFTAlive[_tokenId] = status;

        emit SetNFTbyTokenId(_tokenId, status);
    }
}