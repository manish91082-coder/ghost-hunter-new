// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Phase19Executor} from "../../contracts/Phase19Executor.sol";

interface Vm { function expectRevert() external; }
interface IERC20Fork { function balanceOf(address account) external view returns (uint256); }
interface IQuickSwapRouterForkExec { function getAmountsOut(uint256 amountIn, address[] calldata path) external view returns (uint256[] memory amounts); }
interface IUniswapV3FactoryForkExec { function getPool(address tokenA, address tokenB, uint24 fee) external view returns (address pool); }
interface IUniswapV3QuoterV1ForkExec { function quoteExactInputSingle(address tokenIn, address tokenOut, uint24 fee, uint256 amountIn, uint160 sqrtPriceLimitX96) external returns (uint256 amountOut); }

contract PolygonForkExecutionProbe {
    Vm internal constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    uint256 internal constant POLYGON_CHAIN_ID = 137;
    uint256 internal constant LOAN_USDC = 100_000_000;
    address internal constant AAVE_V3_POOL = 0x794a61358D6845594F94dc1DB02A252b5b4814aD;
    address internal constant QUICKSWAP_V2_ROUTER = 0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff;
    address internal constant QUICKSWAP_V3_ROUTER = 0xf5b509bB0909a69B1c207E495f687a596C168E12;
    address internal constant UNISWAP_V3_ROUTER = 0xE592427A0AEce92De3Edee1F18E0157C05861564;
    address internal constant UNISWAP_V3_QUOTER_V1 = 0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6;
    address internal constant UNISWAP_V3_FACTORY = 0x1F98431c8aD98523631AE4a59f267346ea31F984;
    address internal constant NATIVE_USDC = 0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359;
    address internal constant WMATIC = 0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270;
    bytes32 internal constant QUOTE_ROUTE_HASH = keccak256("fork-probe-quote-route");

    function _findUsableUniswapFee(uint256 amountIn, address tokenIn, address tokenOut) internal returns (uint24 fee, uint256 quote) {
        uint24[4] memory feeTiers = [uint24(100), uint24(500), uint24(3000), uint24(10000)];
        for (uint256 i = 0; i < feeTiers.length; i++) {
            uint24 candidate = feeTiers[i]; address pool = IUniswapV3FactoryForkExec(UNISWAP_V3_FACTORY).getPool(tokenIn, tokenOut, candidate);
            if (pool == address(0) || pool.code.length == 0) continue;
            try IUniswapV3QuoterV1ForkExec(UNISWAP_V3_QUOTER_V1).quoteExactInputSingle(tokenIn, tokenOut, candidate, amountIn, 0) returns (uint256 amountOut) {
                if (amountOut > 0) return (candidate, amountOut);
            } catch {}
        }
        revert("no usable uniswap fee tier");
    }

    function test_real_aave_flashloan_and_dex_callback_path_rolls_back() public {
        require(block.chainid == POLYGON_CHAIN_ID, "not polygon fork"); require(block.number > 0, "no fork block");
        require(AAVE_V3_POOL.code.length > 0, "missing Aave pool"); require(QUICKSWAP_V2_ROUTER.code.length > 0, "missing QuickSwap router"); require(UNISWAP_V3_ROUTER.code.length > 0, "missing Uniswap router");
        require(UNISWAP_V3_QUOTER_V1.code.length > 0, "missing Uniswap quoter"); require(UNISWAP_V3_FACTORY.code.length > 0, "missing Uniswap factory");
        require(IERC20Fork(NATIVE_USDC).balanceOf(AAVE_V3_POOL) > LOAN_USDC, "insufficient Aave USDC liquidity");
        address[] memory quickPath = new address[](2); quickPath[0] = NATIVE_USDC; quickPath[1] = WMATIC;
        uint256[] memory quickQuote = IQuickSwapRouterForkExec(QUICKSWAP_V2_ROUTER).getAmountsOut(LOAN_USDC, quickPath);
        require(quickQuote.length == 2 && quickQuote[0] == LOAN_USDC && quickQuote[1] > 0, "invalid QuickSwap quote");
        (uint24 uniFee, uint256 uniQuote) = _findUsableUniswapFee(quickQuote[1], WMATIC, NATIVE_USDC); require(uniQuote > 0, "invalid Uniswap quote");
        Phase19Executor executor = new Phase19Executor(AAVE_V3_POOL, QUICKSWAP_V2_ROUTER, QUICKSWAP_V3_ROUTER, UNISWAP_V3_ROUTER);
        Phase19Executor.ExecutionParams memory p; p.asset = NATIVE_USDC; p.tokenMid = WMATIC; p.firstOnQuickSwap = true; p.quickSwapVenueKind = 1; p.uniswapFee = uniFee;
        p.amountOutMinFirst = quickQuote[1] * 9 / 10; p.amountOutMinSecond = uniQuote * 9 / 10; p.minimumSurplus = type(uint256).max / 2; p.deadline = block.timestamp + 300; p.routeHash = QUOTE_ROUTE_HASH;
        bytes32 topology = executor.routeTopologyHash(NATIVE_USDC, WMATIC, true, 1, uniFee); p.routeCommitment = executor.routeCommitment(QUOTE_ROUTE_HASH, topology); p.intentHash = keccak256("fork-probe-intent");
        require(IERC20Fork(NATIVE_USDC).balanceOf(address(executor)) == 0, "unexpected executor balance");
        vm.expectRevert(); executor.execute(p, LOAN_USDC);
        require(IERC20Fork(NATIVE_USDC).balanceOf(address(executor)) == 0, "fork rollback left USDC"); require(!executor.activeExecution(), "active state survived rollback"); require(!executor.consumedIntent(p.intentHash), "intent consumed on rollback");
    }
}
