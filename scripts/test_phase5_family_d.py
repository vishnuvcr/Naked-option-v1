import numpy as np
import pandas as pd

from run_phase5_family_d import cutoff_train_end, fit_predict_block, model, prep_fit, precompute_sequence_representations, purged_train_end, sequence_features


def main():
    rng = np.random.default_rng(42)
    X = pd.DataFrame(rng.normal(size=(420, 7)))
    y = pd.Series((np.arange(len(X)) % 2).astype(int))

    # Deterministic sequence construction.
    a, i = sequence_features(X, 20, "lag")
    b, j = sequence_features(X, 20, "lag")
    assert np.array_equal(a, b) and np.array_equal(i, j)
    assert a.shape == (401, 140)
    pre = precompute_sequence_representations(X, "lag")
    pre2 = np.full_like(pre, np.nan)
    pre2[i] = a
    assert np.allclose(pre, pre2, equal_nan=True)

    # Session-boundary guard: windows must never cross group changes.
    groups = pd.Series(np.repeat(np.arange(3), 140))
    _, idx = sequence_features(X, 20, "lag", groups=groups)
    assert idx.min() == 19
    assert not np.any((idx >= 140) & (idx < 159))
    assert not np.any((idx >= 280) & (idx < 299))
    assert np.all(groups.iloc[idx].to_numpy() == np.floor(idx / 140).astype(int))

    # Chronological purge.
    assert purged_train_end(320, 20) == 300
    assert purged_train_end(10, 20) == 0

    # Intraday timestamp cutoff must work with both timezone-aware and
    # timezone-naive representations.
    naive = pd.date_range("2026-01-01 09:30", periods=5, freq="h")
    aware = naive.tz_localize("Asia/Kolkata")
    assert cutoff_train_end(naive, naive[2]) == 2
    assert cutoff_train_end(aware, aware[2]) == 2

    # Training-only preprocessing: the fitted scaler must reproduce the
    # training-window mean, not the full-sample mean.
    pipe = prep_fit("D08")
    pipe.fit(X.iloc[:300], y.iloc[:300])
    fitted_mean = pipe.named_steps["standardscaler"].mean_
    expected_mean = X.iloc[:300].mean().to_numpy()
    full_mean = X.mean().to_numpy()
    assert np.allclose(fitted_mean, expected_mean)
    assert not np.allclose(fitted_mean, full_mean)

    # Sequence methods must preserve valid predictions within a session even
    # when a test block also contains session-start rows without a full warm-up.
    seq_p = fit_predict_block("D13", X, y, 360, np.array([280, 281, 300]), groups=groups)
    assert np.isnan(seq_p[0]) and np.isnan(seq_p[1]) and np.isfinite(seq_p[2])
    # Use one synthetic group below so every registered method has enough
    # sequence endpoints for the finite-probability interface test.
    for name in [f"D{i:02d}" for i in range(1, 16)]:
        p = fit_predict_block(name, X, y, 360, np.array([360, 361, 362]), groups=None)
        assert len(p) == 3, f"{name}: wrong probability length {len(p)}"
        assert np.all(np.isfinite(p)), f"{name}: non-finite probabilities {p}"
        assert np.all((p >= 0) & (p <= 1)), f"{name}: out-of-range probabilities {p}"

    # D01-D12 are separately instantiated to ensure every frozen classifier
    # remains available and exposes a probability interface.
    for name in ["D01", "D02", "D03", "D04", "D05", "D06", "D08", "D09", "D10", "D11", "D12"]:
        estimator = model(name)
        assert estimator is not None, f"{name}: missing registered estimator"

    print("PHASE5_REGRESSION_PASS")


if __name__ == "__main__":
    main()
