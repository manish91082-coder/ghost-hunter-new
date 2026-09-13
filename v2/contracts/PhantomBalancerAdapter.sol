// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title PhantomBalancerAdapter
 * @notice Balancer v2 Vault Flash Loan Callback Adapter for PhantomX MVP.
 * Enables 0.00% Flash Loan Fee routing on Polygon Mainnet.
 * Balancer Vault Address (Polygon): 0xBA12222222228d8Ba445958a75a0704d566BF2C8
 */

interface IERC20 {
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address recipient, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
}

interface IBalancerVault {
    function flashLoan(
        address recipient,
        IERC20[] memory tokens,
        uint256[] memory amounts,
        bytes memory userData
    ) external;
}

contract PhantomBalancerAdapter {
    address public immutable owner;
    IBalancerVault public immutable balancerVault;
    
    // Polygon Mainnet Addresses
    address public constant BALANCER_VAULT_POLYGON = 0xBA12222222228d8Ba445958a75a0704d566BF2C8;
    address public constant USDC_POLYGON           = 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174;

    event FlashLoanExecuted(address indexed token, uint256 amount, uint256 netProfit);

    modifier onlyOwner() {
        require(msg.sender == owner, "NOT_OWNER");
        _;
    }

    constructor() {
        owner = msg.sender;
        balancerVault = IBalancerVault(BALANCER_VAULT_POLYGON);
    }

    /**
     * @notice Initiates zero-fee flash loan from Balancer v2 Vault.
     */
    function requestFlashLoan(address token, uint256 amount, bytes calldata data) external onlyOwner {
        IERC20[] memory tokens = new IERC20[](1);
        tokens[0] = IERC20(token);
        
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = amount;

        balancerVault.flashLoan(address(this), tokens, amounts, data);
    }

    /**
     * @notice Balancer Vault callback function required for 0.00% fee flash loans.
     */
    function receiveFlashLoan(
        IERC20[] memory tokens,
        uint256[] memory amounts,
        uint256[] memory feeAmounts,
        bytes memory userData
    ) external {
        require(msg.sender == address(balancerVault), "INVALID_BALANCER_VAULT");

        IERC20 borrowedToken = tokens[0];
        uint256 loanAmount   = amounts[0];
        uint256 feeAmount    = feeAmounts[0]; // Balancer v2 fee is 0 on Polygon

        uint256 initialBalance = borrowedToken.balanceOf(address(this));

        // Decode userData for trade routing
        (address targetToken, bool startQuickswap, uint256 minOut1, uint256 minOut2) = 
            abi.decode(userData, (address, bool, uint256, uint256));

        // --- ARBITRAGE SWAP EXECUTION HERE ---
        // (Leg 1: USDC -> TargetToken | Leg 2: TargetToken -> USDC)

        uint256 finalBalance = borrowedToken.balanceOf(address(this));
        uint256 totalOwed    = loanAmount + feeAmount;

        // Ground-Truth EVM Atomic Revert Protection
        require(finalBalance >= initialBalance + totalOwed, "INSUFFICIENT_PROFIT_ATOMIC_REVERT");

        // Repay Balancer Vault (0.00% fee)
        borrowedToken.transfer(address(balancerVault), totalOwed);

        emit FlashLoanExecuted(address(borrowedToken), loanAmount, finalBalance - (initialBalance + totalOwed));
    }

    /**
     * @notice Withdraw profits safely to vault.
     */
    function withdrawToken(address token) external onlyOwner {
        uint256 balance = IERC20(token).balanceOf(address(this));
        if (balance > 0) {
            IERC20(token).transfer(owner, balance);
        }
    }
}
