// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20MockRouter {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

contract MockQuickSwapRouter {
    uint256 public rateNumerator;
    uint256 public rateDenominator;
    address public tokenOut;

    constructor(uint256 numerator, uint256 denominator, address tokenOut_) {
        rateNumerator = numerator;
        rateDenominator = denominator;
        tokenOut = tokenOut_;
    }

    function swapExactTokensForTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256
    ) external returns (uint256[] memory amounts) {
        require(path.length == 2, "path");
        require(path[1] == tokenOut, "token");
        uint256 amountOut = (amountIn * rateNumerator) / rateDenominator;
        require(amountOut >= amountOutMin, "slippage");
        require(IERC20MockRouter(path[0]).transferFrom(msg.sender, address(this), amountIn), "in");
        require(IERC20MockRouter(tokenOut).transfer(to, amountOut), "out");
        amounts = new uint256[](2);
        amounts[0] = amountIn;
        amounts[1] = amountOut;
    }
}

contract MockUniswapV3Router {
    uint256 public rateNumerator;
    uint256 public rateDenominator;
    address public tokenOut;

    constructor(uint256 numerator, uint256 denominator, address tokenOut_) {
        rateNumerator = numerator;
        rateDenominator = denominator;
        tokenOut = tokenOut_;
    }

    struct ExactInputSingleParams {
        address tokenIn;
        address tokenOut;
        uint24 fee;
        address recipient;
        uint256 deadline;
        uint256 amountIn;
        uint256 amountOutMinimum;
        uint160 sqrtPriceLimitX96;
    }

    function exactInputSingle(ExactInputSingleParams calldata p) external returns (uint256 amountOut) {
        require(p.tokenOut == tokenOut, "token");
        require(p.fee != 0, "fee");
        require(block.timestamp <= p.deadline, "deadline");
        amountOut = (p.amountIn * rateNumerator) / rateDenominator;
        require(amountOut >= p.amountOutMinimum, "slippage");
        require(IERC20MockRouter(p.tokenIn).transferFrom(msg.sender, address(this), p.amountIn), "in");
        require(IERC20MockRouter(tokenOut).transfer(p.recipient, amountOut), "out");
    }
}
