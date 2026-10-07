from __future__ import annotations

from pathlib import Path
import json
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler, SplineTransformer
from sklearn.pipeline import make_pipeline

from run_phase3_daily_baselines import load_daily, make_label, metrics as daily_metrics
from run_phase3_intraday_baselines import load as load_intraday, labels as intraday_labels, metrics as intra_metrics

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/reports"
OUT.mkdir(parents=True, exist_ok=True)

DAILY_H = [1, 2, 3, 5, 10]
INTRA_H = [5, 15, 30, 60, 120]
SEED = 42
SEQUENCE_WINDOW = 20
N_CONV_FILTERS = 16
ATTN_HEADS = 2
ATTN_HEAD_DIM = 16
ATTN_WIDTH = ATTN_HEADS * ATTN_HEAD_DIM


def features_daily(df: pd.DataFrame) -> pd.DataFrame:
    r = df["ret_1"]
    return pd.DataFrame({
        "ret1": r,
        "ret2": r.shift(1),
        "ret3": r.shift(2),
        "ret5": df["log_close"].diff(5),
        "ret10": df["log_close"].diff(10),
        "vol20": r.rolling(20).std(),
        "gap": df["gap"],
    })


def features_intraday(df: pd.DataFrame) -> pd.DataFrame:
    r = df["log_spot"].diff()
    x = pd.DataFrame({
        "ret1": r,
        "ret2": r.shift(1),
        "ret3": r.shift(2),
        "ret5": df["log_spot"].diff(5),
        "ret10": df["log_spot"].diff(10),
        "vol20": r.rolling(20).std(),
    })
    day_open = df.groupby("date")["spot"].transform("first")
    day_close = df.groupby("date")["spot"].last()
    x["gap"] = np.log(day_open / df["date"].map(day_close.shift(1)))
    return x


def model(name: str):
    if name == "D01":
        return RandomForestClassifier(n_estimators=300, max_depth=6, min_samples_leaf=20, class_weight="balanced", random_state=SEED, n_jobs=-1)
    if name == "D02":
        return ExtraTreesClassifier(n_estimators=300, max_depth=6, min_samples_leaf=20, class_weight="balanced", random_state=SEED, n_jobs=-1)
    if name == "D03":
        return GradientBoostingClassifier(n_estimators=200, learning_rate=0.03, max_depth=2, min_samples_leaf=20, random_state=SEED)
    if name in ("D04", "D05", "D06"):
        return HistGradientBoostingClassifier(
            max_iter=200 if name == "D04" else 250,
            learning_rate=0.03 if name == "D04" else 0.02,
            max_leaf_nodes=15,
            min_samples_leaf=30 if name == "D04" else 40,
            random_state=SEED,
        )
    if name == "D08":
        return LogisticRegression(C=1.0, penalty="elasticnet", l1_ratio=0.5, solver="saga", max_iter=3000, random_state=SEED)
    if name == "D09":
        return make_pipeline(
            SplineTransformer(n_knots=8, degree=3, include_bias=False),
            LogisticRegression(C=1.0, max_iter=2000, solver="lbfgs"),
        )
    if name == "D10":
        return KNeighborsClassifier(n_neighbors=31, weights="distance")
    if name == "D11":
        return SVC(C=1.0, kernel="rbf", gamma="scale", probability=True, random_state=SEED)
    if name == "D12":
        return MLPClassifier(hidden_layer_sizes=(32,), max_iter=250, early_stopping=False, random_state=SEED)
    return None


def prep_fit(name: str):
    if name in {"D08", "D09", "D10", "D11", "D12"}:
        return make_pipeline(StandardScaler(), model(name))
    return model(name)


def purged_train_end(first_test_row: int, horizon: int) -> int:
    return max(0, int(first_test_row) - int(horizon))


def _fixed_conv_filters(n_features: int) -> np.ndarray:
    rng = np.random.default_rng(SEED + 1301 + n_features)
    k = rng.normal(size=(N_CONV_FILTERS, n_features, 3))
    k /= np.maximum(np.linalg.norm(k.reshape(N_CONV_FILTERS, -1), axis=1)[:, None, None], 1e-12)
    return k


def _fixed_attention_projections(n_features: int):
    rng = np.random.default_rng(SEED + 1701 + n_features)
    scale = 1.0 / np.sqrt(max(n_features, 1))
    return (
        rng.normal(0.0, scale, size=(n_features, ATTN_WIDTH)),
        rng.normal(0.0, scale, size=(n_features, ATTN_WIDTH)),
        rng.normal(0.0, scale, size=(n_features, ATTN_WIDTH)),
    )


def sequence_features(
    x: pd.DataFrame,
    window: int = SEQUENCE_WINDOW,
    kind: str = "lag",
    groups: pd.Series | None = None,
):
    a = x.to_numpy(float)
    n, n_features = a.shape
    g = pd.Series(np.zeros(n, dtype=int)) if groups is None else pd.Series(groups).reset_index(drop=True)
    if len(g) != n:
        raise ValueError("group length must match feature rows")

    rows: list[np.ndarray] = []
    idx: list[int] = []

    conv_filters = _fixed_conv_filters(n_features) if kind == "conv" else None
    wq, wk, wv = _fixed_attention_projections(n_features) if kind == "attn" else (None, None, None)

    group_values = g.to_numpy()
    starts = np.flatnonzero(np.r_[True, group_values[1:] != group_values[:-1]])
    ends = np.r_[starts[1:], n]

    for start, end in zip(starts, ends):
        positions = np.arange(start, end, dtype=int)
        for j in range(window - 1, len(positions)):
            pos = positions[j]
            win = a[positions[j - window + 1:j + 1]]
            if not np.isfinite(win).all():
                continue

            if kind == "lag":
                rep = win.reshape(-1)
            elif kind == "conv":
                rep = np.einsum("fct,tc->f", conv_filters, win[-3:])
            elif kind == "attn":
                q = win[-1] @ wq
                k = win @ wk
                v = win @ wv
                head_contexts = []
                for h in range(ATTN_HEADS):
                    sl = slice(h * ATTN_HEAD_DIM, (h + 1) * ATTN_HEAD_DIM)
                    scores = (k[:, sl] @ q[sl]) / np.sqrt(ATTN_HEAD_DIM)
                    scores = scores - np.max(scores)
                    weights = np.exp(scores)
                    denom = weights.sum()
                    if not np.isfinite(denom) or denom <= 0:
                        raise FloatingPointError("invalid causal-attention normalization")
                    weights /= denom
                    head_contexts.append(weights @ v[:, sl])
                rep = np.concatenate(head_contexts)
            else:
                raise ValueError(f"unknown sequence kind: {kind}")

            if np.isfinite(rep).all():
                rows.append(rep)
                idx.append(int(pos))

    if not rows:
        width = {"lag": window * n_features, "conv": N_CONV_FILTERS, "attn": ATTN_WIDTH}[kind]
        return np.empty((0, width)), np.empty(0, dtype=int)

    return np.asarray(rows, dtype=float), np.asarray(idx, dtype=int)


def _finite_training_slice(X: pd.DataFrame, y: pd.Series, train_end: int):
    train = X.iloc[:train_end].copy()
    yy = y.iloc[:train_end].copy()
    mask = yy.notna() & train.notna().all(axis=1)
    return train.loc[mask], yy.loc[mask].astype(int)


def _fit_calibrated_stack(X: pd.DataFrame, y: pd.Series, train_end: int, test_rows: np.ndarray):
    train, yy = _finite_training_slice(X, y, train_end)
    if len(yy) < 300 or yy.nunique() < 2:
        return np.full(len(test_rows), np.nan)

    split = max(200, int(len(train) * 0.8))
    if split >= len(train):
        return np.full(len(test_rows), np.nan)

    base_train, base_y = train.iloc[:split], yy.iloc[:split]
    cal_x, cal_y = train.iloc[split:], yy.iloc[split:]
    if base_y.nunique() < 2 or cal_y.nunique() < 2:
        return np.full(len(test_rows), np.nan)

    base_names = ["D01", "D02", "D03", "D04", "D05", "D06"]
    cal_cols = []
    for sub in base_names:
        m = model(sub)
        m.fit(base_train, base_y)
        cal_cols.append(m.predict_proba(cal_x)[:, 1])

    meta = LogisticRegression(C=1.0, solver="lbfgs", max_iter=2000)
    meta.fit(np.column_stack(cal_cols), cal_y)

    refit_probs = []
    for sub in base_names:
        m = model(sub)
        m.fit(train, yy)
        refit_probs.append(m.predict_proba(X.iloc[test_rows])[:, 1])
    return meta.predict_proba(np.column_stack(refit_probs))[:, 1]


def _fit_sequence_model(name: str, X: pd.DataFrame, y: pd.Series, train_end: int, test_rows: np.ndarray, groups: pd.Series | None):
    kind = {"D13": "lag", "D14": "conv", "D15": "attn"}[name]

    train_groups = None if groups is None else groups.iloc[:train_end].reset_index(drop=True)
    train_rep, train_idx = sequence_features(
        X.iloc[:train_end].reset_index(drop=True),
        SEQUENCE_WINDOW,
        kind,
        train_groups,
    )
    if len(train_rep) < 300:
        return np.full(len(test_rows), np.nan)

    train_y = y.iloc[train_idx].to_numpy()
    finite = np.isfinite(train_rep).all(axis=1) & np.isfinite(train_y)
    train_rep, train_y = train_rep[finite], train_y[finite].astype(int)
    if len(train_y) < 300 or np.unique(train_y).size < 2:
        return np.full(len(test_rows), np.nan)

    max_test = int(np.max(test_rows))
    prefix_groups = None if groups is None else groups.iloc[:max_test + 1].reset_index(drop=True)
    test_rep_all, test_idx_all = sequence_features(
        X.iloc[:max_test + 1].reset_index(drop=True),
        SEQUENCE_WINDOW,
        kind,
        prefix_groups,
    )
    lookup = {int(i): rep for i, rep in zip(test_idx_all, test_rep_all)}
    if any(int(i) not in lookup for i in test_rows):
        return np.full(len(test_rows), np.nan)

    test_rep = np.vstack([lookup[int(i)] for i in test_rows])
    pipe = make_pipeline(
        StandardScaler(),
        MLPClassifier(hidden_layer_sizes=(32,), max_iter=250, early_stopping=False, random_state=SEED),
    )
    pipe.fit(train_rep, train_y)
    return pipe.predict_proba(test_rep)[:, 1]


def fit_predict_block(
    name: str,
    X: pd.DataFrame,
    y: pd.Series,
    train_end: int,
    test_rows: np.ndarray,
    groups: pd.Series | None = None,
):
    if len(test_rows) == 0:
        return np.empty(0)

    if name == "D07":
        return _fit_calibrated_stack(X, y, train_end, test_rows)

    train, yy = _finite_training_slice(X, y, train_end)
    if len(yy) < 300 or yy.nunique() < 2:
        return np.full(len(test_rows), np.nan)

    if name in {"D13", "D14", "D15"}:
        return _fit_sequence_model(name, X, y, train_end, test_rows, groups)

    pipe = prep_fit(name)
    pipe.fit(train, yy)
    return np.asarray(pipe.predict_proba(X.iloc[test_rows])[:, 1], dtype=float)


def _daily_run(df: pd.DataFrame, horizons: list[int]):
    X = features_daily(df)
    result = {}
    for H in horizons:
        y, future = make_label(df, H)
        eval_idx = np.arange(len(df), dtype=int)
        h_out = {}

        for name in [f"D{i:02d}" for i in range(1, 16)]:
            p = np.full(len(df), np.nan)
            status = "EXECUTED"
            for start in range(0, len(eval_idx), 20):
                rows = eval_idx[start:start + 20]
                train_end = purged_train_end(rows[0], H)
                try:
                    p[rows] = fit_predict_block(name, X, y, train_end, rows)
                except Exception as exc:
                    status = "BLOCKED_RUNTIME"
                    p = None
                    h_out[name] = {"status": status, "reason": f"{type(exc).__name__}:{exc}"}
                    break

            if p is not None:
                h_out[name] = daily_metrics(y, p, future)
                h_out[name]["status"] = status
                if name in {"D04", "D05", "D06"}:
                    h_out[name]["implementation_note"] = "provider-independent HistGradientBoosting surrogate"
                elif name in {"D13", "D14", "D15"}:
                    h_out[name]["implementation_note"] = "provider-independent causal sequence architecture with fixed representation and 32-unit dense learner"
        result[str(H)] = h_out
    return result


def _intraday_run(df: pd.DataFrame, horizons: list[int]):
    X_full = features_intraday(df)
    grid = (
        (df["minute_of_day"] >= 570)
        & (df["minute_of_day"] <= 930)
        & (((df["minute_of_day"] - 570) % 60) == 0)
    )
    decision_idx = np.flatnonzero(grid.to_numpy())
    X = X_full.iloc[decision_idx].reset_index(drop=True)
    decision_times = pd.to_datetime(df["timestamp"].iloc[decision_idx]).reset_index(drop=True)
    groups = df["date"].iloc[decision_idx].reset_index(drop=True)

    result = {}
    for H in horizons:
        y_full, future_full, _ = intraday_labels(df["timestamp"], df["spot"], H)
        y = y_full.iloc[decision_idx].reset_index(drop=True)
        future = future_full.iloc[decision_idx].reset_index(drop=True)
        h_out = {}

        for name in [f"D{i:02d}" for i in range(1, 16)]:
            p = np.full(len(X), np.nan)
            status = "EXECUTED"
            for start in range(0, len(X), 20):
                rows = np.arange(start, min(start + 20, len(X)), dtype=int)
                first_time = decision_times.iloc[rows[0]]
                cutoff = first_time - pd.Timedelta(minutes=int(H))
                train_end = int(np.searchsorted(decision_times.to_numpy(), cutoff.to_datetime64(), side="left"))
                try:
                    p[rows] = fit_predict_block(name, X, y, train_end, rows, groups=groups)
                except Exception as exc:
                    status = "BLOCKED_RUNTIME"
                    p = None
                    h_out[name] = {"status": status, "reason": f"{type(exc).__name__}:{exc}"}
                    break

            if p is not None:
                h_out[name] = intra_metrics(y, p, future)
                h_out[name]["status"] = status
                if name in {"D04", "D05", "D06"}:
                    h_out[name]["implementation_note"] = "hourly-grid evaluation with provider-independent HistGradientBoosting surrogate"
                elif name in {"D13", "D14", "D15"}:
                    h_out[name]["implementation_note"] = "hourly-grid causal sequence model; intraday session boundaries enforced"
        result[str(H)] = h_out
    return result


def main():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        d = load_daily()
        daily = _daily_run(d, DAILY_H)
        q = load_intraday()
        q["log_spot"] = np.log(q["spot"])
        intraday = _intraday_run(q, INTRA_H)

    out = {
        "protocol": "research/phase5/MACHINE_LEARNING_PROTOCOL.md",
        "seed": SEED,
        "sequence_window": SEQUENCE_WINDOW,
        "daily": {"rows": len(d), "horizons": daily},
        "intraday": {
            "rows": len(q),
            "hourly_decision_rows": int(((q["minute_of_day"] >= 570) & (q["minute_of_day"] <= 930) & (((q["minute_of_day"] - 570) % 60) == 0)).sum()),
            "horizons": intraday,
        },
    }
    (OUT / "phase5_family_d_results.json").write_text(json.dumps(out, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({"daily_rows": len(d), "intraday_rows": len(q), "status": "PASS"}, indent=2))


if __name__ == "__main__":
    main()
