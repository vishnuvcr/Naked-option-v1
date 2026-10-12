#!/usr/bin/env python3
"""Synthetic-only regression tests. No network, secret, or real market-data use."""
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

path = Path(__file__).with_name("phase8p_greek_prediction.py")
spec = importlib.util.spec_from_file_location("phase8p", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def main():
    result = m.synthetic_self_test()
    assert result["real_artifacts_opened"] is False
    assert result["model_fitted"] is False

    # Paired inference must not silently drop a non-finite row.
    try:
        m.paired_brier_bootstrap([0,1], [.2,np.nan], [.3,.7], 2, reps=10)
    except ValueError as exc:
        assert "non-finite" in str(exc)
    else:
        raise AssertionError("non-finite paired row was silently accepted")

    # Fixed seeds make the bootstrap reproducible.
    y = np.asarray([0,1] * 60, dtype=float)
    p0 = np.where(y == 1, .56, .44)
    p1 = np.where(y == 1, .66, .34)
    a = m.paired_brier_bootstrap(y, p0, p1, 20, reps=100, seed=42)
    b = m.paired_brier_bootstrap(y, p0, p1, 20, reps=100, seed=42)
    assert a == b and a["mean_brier_improvement"] > 0

    # Exact fail-closed authorization contract.
    bad_decisions = [
        (False, True, {"status":"PASS","model_fit_authorized":True,"holdout_access_authorized":False,"option_pnl_authorized":False,"strategy_promotion_authorized":False}),
        (True, False, {"status":"PASS","model_fit_authorized":True,"holdout_access_authorized":False,"option_pnl_authorized":False,"strategy_promotion_authorized":False}),
        (True, True, {"status":"PASS","model_fit_authorized":True,"holdout_access_authorized":True,"option_pnl_authorized":False,"strategy_promotion_authorized":False}),
        (True, True, {"status":"BLOCKED","model_fit_authorized":False,"holdout_access_authorized":False,"option_pnl_authorized":False,"strategy_promotion_authorized":False}),
    ]
    for scope, code, decision in bad_decisions:
        try:
            m.enforce_fit_gate(scope, code, decision)
        except m.GateBlocked:
            pass
        else:
            raise AssertionError("invalid authorization state was accepted")
    print("PASS: Phase 8P synthetic tests; real artifacts untouched; no model fit")

if __name__ == "__main__":
    main()
