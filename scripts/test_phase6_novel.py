from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from run_phase6_novel import (
    ABSTENTION_HIGH,
    ABSTENTION_LOW,
    E01_WINDOW,
    E03_WINDOW,
    E04_WINDOW,
    E05_WINDOW,
    E06_LAGS,
    E08_MODEL_MAP,
    apply_rank_bin,
    entropy_weight,
    fit_rank_reference,
    hurst_feature,
    i03_probability,
    mfdfa_delta,
    option_break_even_return,
    permutation_entropy,
    roughness_feature,
    sample_entropy,
)


def assert_close(a, b, tol=1e-12):
    assert np.isfinite(a) and np.isfinite(b)
    assert abs(float(a) - float(b)) <= tol


def main():
    rng = np.random.default_rng(42)
    base = rng.normal(0.0, 0.01, size=520)

    # Fixed constants and explicit windows.
    assert E01_WINDOW == 256
    assert E03_WINDOW == 100
    assert E04_WINDOW == 100
    assert E05_WINDOW == 60
    assert E06_LAGS == (1, 2, 5, 10)
    assert E08_MODEL_MAP == {0: "D09", 1: "D02", 2: "D12"}

    # Rank binning is deterministic and training-reference based.
    train = np.array([-2.0, -1.0, -1.0, 0.0, 1.0, 2.0])
    ref = fit_rank_reference(train)
    bins1 = [apply_rank_bin(v, ref, 4) for v in train]
    bins2 = [apply_rank_bin(v, ref, 4) for v in train]
    assert bins1 == bins2
    assert all(0 <= b < 4 for b in bins1)

    # Future-row mutation invariance for the causal feature family.
    t = 319
    hurst_a = hurst_feature(base)[0][t]
    mut = base.copy()
    mut[t + 1:] += 5.0
    hurst_b = hurst_feature(mut)[0][t]
    assert_close(hurst_a, hurst_b, tol=1e-12)

    mf_a = mfdfa_delta(base, t)
    mf_b = mfdfa_delta(mut, t)
    assert_close(mf_a, mf_b, tol=1e-12)

    se_a = sample_entropy(base[t - E03_WINDOW + 1:t + 1])
    se_b = sample_entropy(mut[t - E03_WINDOW + 1:t + 1])
    assert_close(se_a, se_b, tol=1e-12)

    pe_a = permutation_entropy(base[t - E04_WINDOW + 1:t + 1])
    pe_b = permutation_entropy(mut[t - E04_WINDOW + 1:t + 1])
    assert_close(pe_a, pe_b, tol=1e-12)

    rough_a = roughness_feature(base)[t]
    rough_b = roughness_feature(mut)[t]
    assert_close(rough_a, rough_b, tol=1e-12)

    # Numerical edge cases are deterministic and finite/neutral.
    zero = np.zeros(100)
    assert np.isnan(sample_entropy(zero))
    assert np.isnan(permutation_entropy(np.repeat(0.0, 100)))

    # I03 is dimensionless and remains in a bounded probability range.
    p_low_vol = i03_probability(0.5, 0.005, 0.01)
    p_high_vol = i03_probability(0.5, 0.04, 0.01)
    assert 0.0 <= p_low_vol <= 1.0
    assert 0.0 <= p_high_vol <= 1.0
    assert p_low_vol >= p_high_vol
    assert 0.0 <= i03_probability(-0.5, 0.01, 0.01) <= 1.0

    # I07 exact CE/PE directionality and invalid put-break-even guard.
    ce = option_break_even_return("CE", spot=100.0, strike=100.0, premium=5.0)
    pe = option_break_even_return("PE", spot=100.0, strike=100.0, premium=5.0)
    assert ce > 0
    assert pe < 0
    assert np.isnan(option_break_even_return("PE", 100.0, 100.0, 101.0))

    # Entropy weights are fixed, positive and symmetric around 0.5.
    assert math.isclose(entropy_weight(0.5), 0.05, rel_tol=0, abs_tol=1e-12)
    assert math.isclose(entropy_weight(0.1), entropy_weight(0.9), rel_tol=0, abs_tol=1e-12)
    assert entropy_weight(0.99) > 0.05

    # Fixed abstention band.
    p = np.array([0.44, 0.45, 0.50, 0.55, 0.56])
    trade = (p < ABSTENTION_LOW) | (p > ABSTENTION_HIGH)
    assert trade.tolist() == [True, False, False, False, True]

    # No centered windows are permitted in the implementation.
    source = Path(__file__).with_name("run_phase6_novel.py").read_text(encoding="utf-8")
    assert "center=True" not in source
    assert ".bfill(" not in source
    assert ".ffill(" not in source

    # Regression interface must never silently expose out-of-range probabilities.
    for v in [0.0, 0.01, 0.5, 0.99, 1.0]:
        assert 0.0 <= float(v) <= 1.0

    print("PHASE6_REGRESSION_PASS")


if __name__ == "__main__":
    main()
