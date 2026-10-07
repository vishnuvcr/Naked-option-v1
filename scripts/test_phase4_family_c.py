from __future__ import annotations

import numpy as np
import pandas as pd

from run_phase4_family_c import (
    fit_ar5,
    ar5_horizon_probability,
    hmm_cumulative_moments,
    kalman_horizon_probs,
    cusum_signal,
)


def main() -> None:
    rng = np.random.default_rng(7)

    # C04: fit a continuous-return AR process and verify finite multi-step probabilities.
    r = np.zeros(250)
    for i in range(5, len(r)):
        r[i] = 0.15 * r[i - 1] - 0.05 * r[i - 2] + rng.normal(0.02, 0.05)
    model = fit_ar5(r)
    p1 = ar5_horizon_probability(model, r, 1)
    p5 = ar5_horizon_probability(model, r, 5)
    assert np.isfinite(p1) and np.isfinite(p5)
    assert 0.0 <= p1 <= 1.0
    assert 0.0 <= p5 <= 1.0

    # C06/C07: horizon-specific cumulative moments must change with H.
    transition = np.array([[0.90, 0.10], [0.20, 0.80]], dtype=float)
    means = np.array([-0.02, 0.03], dtype=float)
    variances = np.array([0.01, 0.01], dtype=float)
    m1, q1 = hmm_cumulative_moments(transition, means, variances, 1)
    m4, q4 = hmm_cumulative_moments(transition, means, variances, 4)
    assert np.all(np.isfinite(m1)) and np.all(np.isfinite(q1))
    assert np.all(np.isfinite(m4)) and np.all(np.isfinite(q4))
    assert not np.allclose(m1, m4), "HMM cumulative forecast must be horizon specific"

    # C08: a persistent positive trend should yield P(future price > current price) > 0.5.
    train_price = np.exp(np.linspace(0.0, 1.0, 150))
    test_price = np.exp(np.linspace(1.01, 1.15, 30))
    pk = kalman_horizon_probs(train_price, test_price, 10)
    assert np.all(np.isfinite(pk))
    assert float(np.median(pk)) > 0.5

    # C09: once a direction is detected it must persist until the opposite reset.
    rng2 = np.random.default_rng(19)
    train = pd.Series(rng2.normal(0.0, 0.01, 200))
    test = np.array([0.08, 0.01, 0.005, 0.0, -0.08], dtype=float)
    pc = cusum_signal(train, test)
    assert np.all(pc[:4] >= 0.50)
    assert pc[4] < 0.50

    print("PASS: Family C synthetic horizon/state regression tests")


if __name__ == "__main__":
    main()
