// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Phase19Executor} from "../../contracts/Phase19Executor.sol";
import {MockERC20} from "../../contracts/test/MockERC20.sol";
import {MockAavePool} from "../../contracts/test/MockAavePool.sol";
import {MockQuickSwapRouter, MockUniswapV3Router} from "../../contracts/test/MockRouters.sol";

interface Vm {
    function warp(uint256) external;
    function expectRevert(bytes4) external;
}

contract Phase19ExecutorTest {
    Vm internal constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));

    MockERC20 internal asset;
    MockERC20 internal mid;
    MockAavePool internal pool;
    MockQuickSwapRouter internal quick;
    MockUniswapV3Router internal uni;
    Phase19Executor internal executor;

    uint256 internal constant LOAN = 100 ether;
    uint256 internal constant PREMIUM_BPS = 100;
    uint256 internal constant MIN_SURPLUS = 4 ether;

    function setUp() public {
        asset = new MockERC20("Asset", "AST", 18);
        mid = new MockERC20("Middle", "MID", 18);
        pool = new MockAavePool(PREMIUM_BPS);
        quick = new MockQuickSwapRouter(110, 100, address(mid));
        uni = new MockUniswapV3Router(106, 110, address(asset));
        executor = new Phase19Executor(address(pool), address(quick), address(uni));

        asset.mint(address(pool), 1_000_000 ether);
        mid.mint(address(quick), 1_000_000 ether);
        asset.mint(address(uni), 1_000_000 ether);
        vm.warp(1_000_000);
    }

    function _params(bytes32 intent) internal view returns (Phase19Executor.ExecutionParams memory p) {
        p.asset = address(asset);
        p.tokenMid = address(mid);
        p.firstOnQuickSwap = true;
        p.uniswapFee = 3000;
        p.amountOutMinFirst = 110 ether;
        p.amountOutMinSecond = 106 ether;
        p.minimumSurplus = MIN_SURPLUS;
        p.deadline = 1_000_600;
        p.routeHash = executor.routeHash(address(asset), address(mid), true, 3000);
        p.intentHash = intent;
    }

    function test_execute_real_callback_swap_repay_and_settlement() public {
        Phase19Executor.ExecutionParams memory p = _params(bytes32(uint256(1)));
        uint256 beforeBalance = asset.balanceOf(address(executor));
        executor.execute(p, LOAN);

        // 100 -> 110 -> 106, then 101 repayment, leaving 5 token surplus.
        require(asset.balanceOf(address(executor)) == beforeBalance + 5 ether, "surplus");
        require(pool != address(0), "pool fixture");
        require(executor.consumedIntent(p.intentHash), "intent not consumed");
        require(!executor.activeExecution(), "execution still active");
    }

    function test_callback_spoof_is_rejected() public {
        Phase19Executor.ExecutionParams memory p = _params(bytes32(uint256(2)));
        bytes memory encoded = abi.encode(p, LOAN);
        vm.expectRevert(Phase19Executor.InvalidCaller.selector);
        executor.executeOperation(address(asset), LOAN, 1 ether, address(executor), encoded);
    }

    function test_bad_initiator_is_rejected() public {
        Phase19Executor.ExecutionParams memory p = _params(bytes32(uint256(3)));
        pool.setForceBadInitiator(true);
        vm.expectRevert(Phase19Executor.InvalidInitiator.selector);
        executor.execute(p, LOAN);
    }

    function test_route_mutation_is_rejected() public {
        Phase19Executor.ExecutionParams memory p = _params(bytes32(uint256(4)));
        p.tokenMid = address(asset);
        vm.expectRevert(Phase19Executor.InvalidRoute.selector);
        executor.execute(p, LOAN);
    }

    function test_replay_is_rejected() public {
        Phase19Executor.ExecutionParams memory p = _params(bytes32(uint256(5)));
        executor.execute(p, LOAN);
        vm.expectRevert(Phase19Executor.InvalidRoute.selector);
        executor.execute(p, LOAN);
    }

    function test_existing_balance_cannot_subsidize_minimum_surplus() public {
        asset.mint(address(executor), 100 ether);
        Phase19Executor.ExecutionParams memory p = _params(bytes32(uint256(6)));
        p.minimumSurplus = 1 ether;
        quick = new MockQuickSwapRouter(100, 100, address(mid));
        uni = new MockUniswapV3Router(101, 100, address(asset));
        executor = new Phase19Executor(address(pool), address(quick), address(uni));
        mid.mint(address(quick), 1_000_000 ether);
        asset.mint(address(uni), 1_000_000 ether);
        p.routeHash = executor.routeHash(address(asset), address(mid), true, 3000);
        p.amountOutMinFirst = 100 ether;
        p.amountOutMinSecond = 101 ether;
        vm.expectRevert(Phase19Executor.MinimumSurplusFailed.selector);
        executor.execute(p, LOAN);
    }

    function test_insufficient_second_leg_output_reverts_atomically() public {
        Phase19Executor.ExecutionParams memory p = _params(bytes32(uint256(7)));
        p.amountOutMinSecond = 107 ether;
        vm.expectRevert(Phase19Executor.MinimumOutputFailed.selector);
        executor.execute(p, LOAN);
        require(asset.balanceOf(address(executor)) == 0, "rollback failed");
        require(!executor.consumedIntent(p.intentHash), "intent consumed on revert");
    }
}
