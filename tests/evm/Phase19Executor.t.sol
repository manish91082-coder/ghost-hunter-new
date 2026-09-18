// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Phase19Executor} from "../../contracts/Phase19Executor.sol";
import {MockERC20} from "../../contracts/test/MockERC20.sol";
import {MockAavePool} from "../../contracts/test/MockAavePool.sol";
import {MockQuickSwapRouter, MockQuickSwapV3Router, MockUniswapV3Router} from "../../contracts/test/MockRouters.sol";

interface Vm { function warp(uint256) external; function chainId(uint256) external; function expectRevert() external; function expectRevert(bytes4) external; }

contract ExecutorAttacker {
    function attempt(Phase19Executor executor, Phase19Executor.ExecutionParams calldata p, uint256 amount) external { executor.execute(p, amount); }
}

contract Phase19ExecutorTest {
    Vm internal constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    MockERC20 internal asset; MockERC20 internal mid; MockAavePool internal pool; MockQuickSwapRouter internal quick; MockQuickSwapV3Router internal quickV3; MockUniswapV3Router internal uni; Phase19Executor internal executor;
    uint256 internal constant LOAN = 100 ether; uint256 internal constant PREMIUM_BPS = 100; uint256 internal constant MIN_SURPLUS = 4 ether;
    bytes32 internal constant QUOTE_ROUTE_HASH = keccak256("canonical-quote-route");

    function setUp() public {
        vm.chainId(137);
        asset = new MockERC20("Asset", "AST", 18); mid = new MockERC20("Middle", "MID", 18); pool = new MockAavePool(PREMIUM_BPS);
        quick = new MockQuickSwapRouter(110, 100, address(mid)); quickV3 = new MockQuickSwapV3Router(110, 100, address(mid)); uni = new MockUniswapV3Router(106, 110, address(asset));
        executor = new Phase19Executor(address(pool), address(quick), address(quickV3), address(uni));
        asset.mint(address(pool), 1_000_000 ether); mid.mint(address(quick), 1_000_000 ether); asset.mint(address(uni), 1_000_000 ether); vm.warp(1_000_000);
    }

    function _params(bytes32 intent) internal view returns (Phase19Executor.ExecutionParams memory p) {
        p.asset = address(asset); p.tokenMid = address(mid); p.firstOnQuickSwap = true; p.quickSwapVenueKind = 1; p.uniswapFee = 3000; p.amountOutMinFirst = 110 ether; p.amountOutMinSecond = 106 ether;
        p.minimumSurplus = MIN_SURPLUS; p.deadline = 1_000_600; p.routeHash = QUOTE_ROUTE_HASH;
        p.routeCommitment = executor.routeCommitment(p.routeHash, executor.routeTopologyHash(address(asset), address(mid), true, 1, 3000)); p.intentHash = intent;
    }

    function test_execute_quickswap_v3_real_callback_swap_repay_and_settlement() public {
        Phase19Executor.ExecutionParams memory p = _params(bytes32(uint256(14)));
        p.quickSwapVenueKind = 2;
        p.routeCommitment = executor.routeCommitment(p.routeHash, executor.routeTopologyHash(address(asset), address(mid), true, 2, 3000));
        executor.execute(p, LOAN);
        require(asset.balanceOf(address(executor)) == 5 ether, "v3 surplus");
        require(executor.consumedIntent(p.intentHash), "v3 intent not consumed");
        require(asset.allowance(address(executor), address(quickV3)) == 0, "v3 approval not reset");
    }

    function test_execute_real_callback_swap_repay_and_settlement() public {
        Phase19Executor.ExecutionParams memory p = _params(bytes32(uint256(1))); uint256 beforeBalance = asset.balanceOf(address(executor)); executor.execute(p, LOAN);
        require(asset.balanceOf(address(executor)) == beforeBalance + 5 ether, "surplus"); require(executor.consumedIntent(p.intentHash), "intent not consumed"); require(!executor.activeExecution(), "execution still active");
        require(asset.allowance(address(executor), address(quick)) == 0, "quick approval not reset"); require(asset.allowance(address(executor), address(uni)) == 0, "uni approval not reset");
    }

    function test_execute_reverse_route_real_callback_swap_repay_and_settlement() public {
        uni = new MockUniswapV3Router(110, 100, address(mid)); quick = new MockQuickSwapRouter(106, 110, address(asset)); mid.mint(address(uni), 1_000_000 ether); asset.mint(address(quick), 1_000_000 ether);
        executor = new Phase19Executor(address(pool), address(quick), address(uni)); Phase19Executor.ExecutionParams memory p = _params(bytes32(uint256(8))); p.firstOnQuickSwap = false; p.amountOutMinFirst = 110 ether; p.amountOutMinSecond = 106 ether;
        p.routeCommitment = executor.routeCommitment(p.routeHash, executor.routeTopologyHash(address(asset), address(mid), false, 1, 3000)); executor.execute(p, LOAN); require(asset.balanceOf(address(executor)) == 5 ether, "reverse surplus"); require(executor.consumedIntent(p.intentHash), "reverse intent not consumed");
    }

    function test_only_owner_is_enforced() public { ExecutorAttacker attacker = new ExecutorAttacker(); Phase19Executor.ExecutionParams memory p = _params(bytes32(uint256(9))); (bool ok,) = address(attacker).call(abi.encodeWithSelector(ExecutorAttacker.attempt.selector, executor, p, LOAN)); require(!ok, "non-owner executed"); require(!executor.activeExecution(), "unauthorized execution activated"); }

    function test_callback_spoof_is_rejected() public { Phase19Executor.ExecutionParams memory p = _params(bytes32(uint256(2))); bytes memory encoded = abi.encode(p, LOAN); vm.expectRevert(Phase19Executor.InvalidCaller.selector); executor.executeOperation(address(asset), LOAN, 1 ether, address(executor), encoded); }

    function test_bad_initiator_is_rejected() public { Phase19Executor.ExecutionParams memory p = _params(bytes32(uint256(3))); pool.setForceBadInitiator(true); vm.expectRevert(Phase19Executor.InvalidInitiator.selector); executor.execute(p, LOAN); }

    function test_route_mutation_is_rejected() public { Phase19Executor.ExecutionParams memory p = _params(bytes32(uint256(4))); p.tokenMid = address(asset); vm.expectRevert(Phase19Executor.InvalidRoute.selector); executor.execute(p, LOAN); }

    function test_quote_route_hash_is_required() public { Phase19Executor.ExecutionParams memory p = _params(bytes32(uint256(11))); p.routeHash = bytes32(0); vm.expectRevert(Phase19Executor.InvalidRoute.selector); executor.execute(p, LOAN); }

    function test_route_commitment_mutation_is_rejected() public { Phase19Executor.ExecutionParams memory p = _params(bytes32(uint256(12))); p.routeCommitment = bytes32(uint256(999)); vm.expectRevert(Phase19Executor.InvalidRoute.selector); executor.execute(p, LOAN); }

    function test_quote_route_mutation_requires_new_commitment() public { Phase19Executor.ExecutionParams memory p = _params(bytes32(uint256(13))); p.routeHash = keccak256("mutated-quote-route"); vm.expectRevert(Phase19Executor.InvalidRoute.selector); executor.execute(p, LOAN); }

    function test_replay_is_rejected() public { Phase19Executor.ExecutionParams memory p = _params(bytes32(uint256(5))); executor.execute(p, LOAN); vm.expectRevert(Phase19Executor.InvalidRoute.selector); executor.execute(p, LOAN); }

    function test_existing_balance_cannot_subsidize_minimum_surplus() public {
        quick = new MockQuickSwapRouter(100, 100, address(mid)); uni = new MockUniswapV3Router(101, 100, address(asset)); executor = new Phase19Executor(address(pool), address(quick), address(uni));
        mid.mint(address(quick), 1_000_000 ether); asset.mint(address(uni), 1_000_000 ether); asset.mint(address(executor), 100 ether);
        Phase19Executor.ExecutionParams memory p = _params(bytes32(uint256(6))); p.minimumSurplus = 1 ether; p.amountOutMinFirst = 100 ether; p.amountOutMinSecond = 101 ether;
        p.routeCommitment = executor.routeCommitment(p.routeHash, executor.routeTopologyHash(address(asset), address(mid), true, 1, 3000)); vm.expectRevert(Phase19Executor.MinimumSurplusFailed.selector); executor.execute(p, LOAN);
    }

    function test_insufficient_second_leg_output_reverts_atomically() public { Phase19Executor.ExecutionParams memory p = _params(bytes32(uint256(7))); p.amountOutMinSecond = 107 ether; vm.expectRevert(); executor.execute(p, LOAN); require(asset.balanceOf(address(executor)) == 0, "rollback failed"); require(!executor.consumedIntent(p.intentHash), "intent consumed on revert"); }

    function test_expired_deadline_is_rejected_before_flash_loan() public { Phase19Executor.ExecutionParams memory p = _params(bytes32(uint256(10))); p.deadline = 999_999; vm.expectRevert(Phase19Executor.InvalidDeadline.selector); executor.execute(p, LOAN); require(!executor.activeExecution(), "expired execution activated"); }

    function test_solidity_route_commitment_reference_vectors_match_python() public {
        uint256 chainId = 137;
        address fixedExecutor = 0x3333333333333333333333333333333333333333;
        address fixedAsset = 0x1111111111111111111111111111111111111111;
        address fixedMid = 0x2222222222222222222222222222222222222222;
        address fixedAave = 0x5555555555555555555555555555555555555555;
        address fixedQuick = 0x6666666666666666666666666666666666666666;
        address fixedQuickV3 = 0x8888888888888888888888888888888888888888;
        address fixedUni = 0x7777777777777777777777777777777777777777;
        bytes32 routeHash = 0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa;
        bytes32 topology = keccak256(abi.encode(chainId, fixedExecutor, fixedAsset, fixedMid, true, uint8(1), uint24(3000), fixedAave, fixedQuick, fixedQuickV3, fixedUni));
        bytes32 commitment = keccak256(abi.encode(routeHash, topology));
        require(topology == 0xf0149b56c3d98c97f486923e1175682fddae24d0b3c7b579d4c23a9117384966, "topology vector mismatch");
        require(commitment == 0x37dfe183ddf63ba6fe10764a8fb8a94c54d4abb4b9c547d92e6adc423a98718d, "commitment vector mismatch");
        require(executor.routeCommitment(routeHash, topology) == commitment, "route commitment mismatch");
    }
}
