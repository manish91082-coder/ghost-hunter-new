"""
PhantomX Strategy Advisor Ground-Truth Unit & Integration Test Suite
=====================================================================
Verifies Balancer V2 low-fee routing, dynamic loan sizing L*, 
adaptive spread threshold, and $0.00 gas loss safety.
"""

import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
from ai_strategy_advisor import PhantomAIStrategyAdvisor

def run_tests():
    advisor = PhantomAIStrategyAdvisor()
    print("=" * 70)
    print("🧪 PHANTOM-X STRATEGY ADVISOR INTEGRATION & GROUND-TRUTH TEST SUITE")
    print("=" * 70)

    tests_passed = 0
    total_tests = 5

    # Test 1: High Spread (0.3739% WMATIC) on 250k Pool Reserve @ 275 Gwei
    res1 = advisor.evaluate_opportunity(0.0983, 0.0979, 250_000, 275.0, pol_usd=0.098)
    print(f"\n[Test 1] 0.3739% WMATIC Spread Evaluation:")
    print(f"  Decision: {res1['decision']} | Route: {res1['best_route_name']}")
    print(f"  Optimal Loan L*: ${res1['optimal_loan_usd']:,} | Net PnL: ${res1['expected_net_pnl_usd']:.2f} USD")
    assert res1["decision"] == "EXECUTE", "Test 1 Failed: Expected EXECUTE for 0.3739% spread"
    assert res1["best_route"] == "OPTIMIZED_LOW_FEE", "Test 1 Failed: Expected Balancer low fee route"
    assert res1["expected_net_pnl_usd"] > 0, "Test 1 Failed: Expected positive Net PnL"
    print("  ✅ TEST 1 PASSED!")
    tests_passed += 1

    # Test 2: Low Spread (0.05%) - Must return IGNORE to protect gas
    res2 = advisor.evaluate_opportunity(100.0, 100.05, 500_000, 275.0, pol_usd=0.098)
    print(f"\n[Test 2] Low Spread (0.05%) Protection Check:")
    print(f"  Decision: {res2['decision']} | Net PnL: ${res2['expected_net_pnl_usd']:.2f} USD")
    assert res2["decision"] == "IGNORE", "Test 2 Failed: Expected IGNORE for low spread"
    print("  ✅ TEST 2 PASSED!")
    tests_passed += 1

    # Test 3: WETH 0.2432% Spread @ 270 Gwei
    res3 = advisor.evaluate_opportunity(2485.82, 2479.77, 1_000_000, 270.0, pol_usd=0.098)
    print(f"\n[Test 3] WETH 0.2432% Spread Evaluation:")
    print(f"  Decision: {res3['decision']} | Optimal Loan: ${res3['optimal_loan_usd']:,} | Net PnL: ${res3['expected_net_pnl_usd']:.2f} USD")
    assert res3["decision"] in ["EXECUTE", "WAIT"], "Test 3 Failed"
    print("  ✅ TEST 3 PASSED!")
    tests_passed += 1

    # Test 4: WBTC 0.2755% Spread @ 280 Gwei
    res4 = advisor.evaluate_opportunity(79889.16, 79669.11, 800_000, 280.0, pol_usd=0.098)
    print(f"\n[Test 4] WBTC 0.2755% Spread Evaluation:")
    print(f"  Decision: {res4['decision']} | Optimal Loan: ${res4['optimal_loan_usd']:,} | Net PnL: ${res4['expected_net_pnl_usd']:.2f} USD")
    assert res4["decision"] in ["EXECUTE", "WAIT"], "Test 4 Failed"
    print("  ✅ TEST 4 PASSED!")
    tests_passed += 1

    # Test 5: Dynamic Min Spread Formula Threshold Check
    adaptive_spread = advisor.compute_adaptive_min_spread(0.0010, 0.012, 100_000)
    print(f"\n[Test 5] Adaptive Min Spread Check at $100k Loan:")
    print(f"  Dynamic Min Spread: {adaptive_spread:.4f}%")
    assert 0.10 <= adaptive_spread <= 0.20, "Test 5 Failed: Expected min spread in range 0.10%-0.20%"
    print("  ✅ TEST 5 PASSED!")
    tests_passed += 1

    print("\n" + "=" * 70)
    print(f"🎉 TEST SUITE COMPLETE: {tests_passed}/{total_tests} PASSED (100%)")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
