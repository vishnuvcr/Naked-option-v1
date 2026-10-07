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

    # Intraday sequence representations are built on the full 1-minute
    # path and then mapped to hourly decision rows. A 20-observation warm-up
    # must be available within a session, while later-session rows must not
    # inherit observations from the prior session.
    X_min = pd.DataFrame(rng.normal(size=(140, 7)))
    g_min = pd.Series(np.r_[np.zeros(70, dtype=int), np.ones(70, dtype=int)])
    for kind in ["lag", "conv", "attn"]:
        full_rep = precompute_sequence_representations(X_min, kind, g_min)
        mapped = full_rep[[60, 69, 89, 119]]
        assert np.isfinite(mapped[0]).all() and np.isfinite(mapped[1]).all()
        assert np.isfinite(mapped[2]).all() and np.isfinite(mapped[3]).all()
        X_mut = X_min.copy()
        X_mut.iloc[70:] += 1000.0
        full_rep_mut = precompute_sequence_representations(X_mut, kind, g_min)
        assert np.allclose(full_rep[69], full_rep_mut[69], equal_nan=True)
        assert not np.isfinite(full_rep[70:89]).any()
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

    # D07 calibrated-meta-stack pin: independently reconstruct the fixed
    # chronological 80/20 stack and confirm the production output matches.
    from sklearn.linear_model import LogisticRegression

    X7 = pd.DataFrame(rng.normal(size=(360, 7)))
    y7 = pd.Series((rng.normal(size=360) > 0).astype(int))
    test_rows7 = np.array([330, 331, 332])
    train_end7 = 300
    produced7 = fit_predict_block("D07", X7, y7, train_end7, test_rows7)

    train7 = X7.iloc[:train_end7].copy()
    yy7 = y7.iloc[:train_end7].copy().astype(int)
    split7 = max(200, int(len(train7) * 0.8))
    base_x7, base_y7 = train7.iloc[:split7], yy7.iloc[:split7]
    cal_x7, cal_y7 = train7.iloc[split7:], yy7.iloc[split7:]
    cal_cols7 = []
    for sub in ["D01", "D02", "D03", "D04", "D05", "D06"]:
        m7 = model(sub)
        m7.fit(base_x7, base_y7)
        cal_cols7.append(m7.predict_proba(cal_x7)[:, 1])
    meta7 = LogisticRegression(C=1.0, solver="lbfgs", max_iter=2000)
    meta7.fit(np.column_stack(cal_cols7), cal_y7)
    refit_cols7 = []
    for sub in ["D01", "D02", "D03", "D04", "D05", "D06"]:
        m7 = model(sub)
        m7.fit(train7, yy7)
        refit_cols7.append(m7.predict_proba(X7.iloc[test_rows7])[:, 1])
    expected7 = meta7.predict_proba(np.column_stack(refit_cols7))[:, 1]
    assert np.allclose(produced7, expected7, rtol=1e-10, atol=1e-12)

    # Post-cutoff labels must not affect D07 test probabilities.
    y7_mut = y7.copy()
    y7_mut.iloc[train_end7:] = 1 - y7_mut.iloc[train_end7:].astype(int)
    produced7_mut = fit_predict_block("D07", X7, y7_mut, train_end7, test_rows7)
    assert np.allclose(produced7, produced7_mut, rtol=1e-10, atol=1e-12)

    # D01-D12 are separately instantiated to ensure every frozen classifier
    # remains available and exposes a probability interface.
    for name in ["D01", "D02", "D03", "D04", "D05", "D06", "D08", "D09", "D10", "D11", "D12"]:
        estimator = model(name)
        assert estimator is not None, f"{name}: missing registered estimator"

    print("PHASE5_REGRESSION_PASS")


if __name__ == "__main__":
    main()
