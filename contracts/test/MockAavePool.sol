// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20MockPool {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

interface IFlashReceiverMock {
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external returns (bool);
}

contract MockAavePool {
    uint256 public premiumBps;
    bool public forceBadInitiator;

    constructor(uint256 premiumBps_) {
        premiumBps = premiumBps_;
    }

    function setForceBadInitiator(bool value) external {
        forceBadInitiator = value;
    }

    function flashLoanSimple(
        address receiverAddress,
        address asset,
        uint256 amount,
        bytes calldata params,
        uint16
    ) external {
        uint256 premium = (amount * premiumBps) / 10_000;
        require(IERC20MockPool(asset).transfer(receiverAddress, amount), "loan transfer");
        address initiator = forceBadInitiator ? address(0xBEEF) : receiverAddress;
        require(IFlashReceiverMock(receiverAddress).executeOperation(asset, amount, premium, initiator, params), "callback");
        require(IERC20MockPool(asset).transferFrom(receiverAddress, address(this), amount + premium), "repayment");
    }
}
