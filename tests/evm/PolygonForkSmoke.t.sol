// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IQuickSwapRouterFork {
    function getAmountsOut(uint256 amountIn, address[] calldata path) external view returns (uint256[] memory amounts);
}

interface IUniswapV3FactoryFork {
    function getPool(address tokenA, address tokenB, uint24 fee) external view returns (address pool);
}

interface IUniswapV3QuoterV1Fork {
    function quoteExactInputSingle(
        address tokenIn,
        address tokenOut,
        uint24 fee,
        uint256 amountIn,
        uint160 sqrtPriceLimitX96
    ) external returns (uint256 amountOut);
}

/// @notice Read-only Polygon fork smoke test against the configured production protocol addresses.
/// @dev This deliberately does not execute a flash loan or submit a transaction. It proves that
///      the fork contains the configured Aave/QuickSwap/Uniswap deployments and that the exact
///      quote surfaces used by Phase-19 can read live fork state.
contract PolygonForkSmokeTest {
    uint256 internal constant POLYGON_CHAIN_ID = 137;
    address internal constant AAVE_V3_POOL = 0x794a61358D6845594F94dc1DB02A252b5b4814aD;
    address internal constant QUICKSWAP_V2_ROUTER = 0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff;
    address internal constant UNISWAP_V3_ROUTER = 0xE592427A0AEce92De3Edee1F18E0157C05861564;
    address internal constant UNISWAP_V3_QUOTER_V1 = 0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6;
    address internal constant UNISWAP_V3_FACTORY = 0x1F98431c8aD98523631AE4a59f267346ea31F984;
    address internal constant USDC = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48;
    address internal constant WMATIC = 0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270;
    address internal constant WETH = 0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619;

    function test_polygon_chain_and_protocol_deployments_exist() public view {
        require(block.chainid == POLYGON_CHAIN_ID, "not polygon fork");
        require(block.number > 0, "no fork block");
        require(AAVE_V3_POOL.code.length > 0, "missing Aave pool");
        require(QUICKSWAP_V2_ROUTER.code.length > 0, "missing QuickSwap router");
        require(UNISWAP_V3_ROUTER.code.length > 0, "missing Uniswap router");
        require(UNISWAP_V3_QUOTER_V1.code.length > 0, "missing Uniswap quoter");
        require(UNISWAP_V3_FACTORY.code.length > 0, "missing Uniswap factory");
        require(USDC.code.length > 0, "missing USDC");
        require(WMATIC.code.length > 0, "missing WMATIC");
        require(WETH.code.length > 0, "missing WETH");
    }

    function test_quickswap_exact_quote_reads_current_fork_state() public view {
        require(block.chainid == POLYGON_CHAIN_ID, "not polygon fork");
        address[] memory path = new address[](2);
        path[0] = USDC;
        path[1] = WMATIC;
        uint256[] memory amounts = IQuickSwapRouterFork(QUICKSWAP_V2_ROUTER).getAmountsOut(1_000_000, path);
        require(amounts.length == 2, "bad QuickSwap quote length");
        require(amounts[0] == 1_000_000, "QuickSwap input mismatch");
        require(amounts[1] > 0, "QuickSwap zero output");
    }

    function test_uniswap_factory_and_quoter_read_current_fork_state() public {
        require(block.chainid == POLYGON_CHAIN_ID, "not polygon fork");
        address pool = IUniswapV3FactoryFork(UNISWAP_V3_FACTORY).getPool(USDC, WETH, 500);
        require(pool != address(0), "missing USDC/WETH 500 pool");
        require(pool.code.length > 0, "missing Uniswap pool code");

        uint256 amountOut = IUniswapV3QuoterV1Fork(UNISWAP_V3_QUOTER_V1).quoteExactInputSingle(
            USDC,
            WETH,
            500,
            1_000_000,
            0
        );
        require(amountOut > 0, "Uniswap zero quote");
    }
}
