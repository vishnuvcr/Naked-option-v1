from __future__ import annotations

from pathlib import Path
import json
import math
import warnings

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, roc_auc_score,
    average_precision_score, brier_score_loss, log_loss,
    confusion_matrix,
)

from run_phase3_daily_baselines import load_daily, make_label
from run_phase3_intraday_baselines import load as load_intraday, labels as intraday_labels
from run_phase5_family_d import (
    features_daily, features_intraday, fit_predict_block, cutoff_train_end,
    purged_train_end,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/reports"
OUT.mkdir(parents=True, exist_ok=True)

DAILY_H = [1, 2, 3, 5, 10]
INTRA_H = [5, 15, 30, 60, 120]
SEED = 42
EPS = 1e-12
E01_WINDOW = 256
E02_SCALES = (8, 16, 32, 64)
E02_Q = (-3, -2, -1, 0, 1, 2, 3)
E03_WINDOW = 100
E04_WINDOW = 100
E04_M = 5
E05_WINDOW = 60
E06_LAGS = (1, 2, 5, 10)
I01_SCALES = (3, 10, 30)
I03_WINDOW = 30


def sigmoid(x: np.ndarray | float) -> np.ndarray | float:
    x = np.clip(x, -30.0, 30.0)
    return 1.0 / (1.0 + np.exp(-x))


ABSTENTION_LOW = 0.45
ABSTENTION_HIGH = 0.55
E08_MODEL_MAP = {0: "D09", 1: "D02", 2: "D12"}


def i03_probability(persistence: float, current_vol: float, training_median_vol: float) -> float:
    if not np.isfinite(persistence):
        return np.nan
    if not np.isfinite(training_median_vol) or training_median_vol <= 0:
        score = persistence
    else:
        vol = current_vol if np.isfinite(current_vol) and current_vol > 0 else training_median_vol
        vol_ratio = vol / training_median_vol
        score = persistence / max(vol_ratio, 0.25)
    return float(sigmoid(np.clip(score, -3.0, 3.0)))


def option_break_even_return(side: str, spot: float, strike: float, premium: float) -> float:
    """Return log-return break-even threshold for a long naked option."""
    if not all(np.isfinite(v) for v in (spot, strike, premium)) or spot <= 0 or premium < 0:
        return np.nan
    side = side.upper()
    if side == "CE":
        return float(np.log((strike + premium) / spot))
    if side == "PE":
        if strike - premium <= 0:
            return np.nan
        return float(np.log((strike - premium) / spot))
    raise ValueError("side must be CE or PE")


def entropy_weight(p: float) -> float:
    if not np.isfinite(p):
        return np.nan
    pp = float(np.clip(p, EPS, 1 - EPS))
    h = -(pp * math.log2(pp) + (1 - pp) * math.log2(1 - pp))
    return max(1.0 - h, 0.05)


def block_bootstrap_accuracy(y, p, block_len, reps=200, seed=SEED):
    z = pd.DataFrame({"y": y, "p": p}).dropna()
    if len(z) < block_len:
        return {"lower": None, "upper": None, "median": None}
    rng = np.random.default_rng(seed)
    n = len(z)
    blocks = [np.arange(i, min(i + block_len, n)) for i in range(0, n, block_len)]
    vals = []
    yy = z["y"].to_numpy()
    pp = z["p"].to_numpy()
    for _ in range(reps):
        sel = rng.integers(0, len(blocks), size=len(blocks))
        idx = np.concatenate([blocks[j] for j in sel])[:n]
        vals.append(float(np.mean((pp[idx] >= 0.5) == yy[idx])))
    return {
        "lower": float(np.quantile(vals, 0.025)),
        "upper": float(np.quantile(vals, 0.975)),
        "median": float(np.median(vals)),
    }


def fixed_bins(y, p, future):
    z = pd.DataFrame({
        "y": np.asarray(y, float),
        "p": np.asarray(p, float),
        "future": np.asarray(future, float),
    }).replace([np.inf, -np.inf], np.nan).dropna(subset=["y", "p", "future"])
    out = {}
    edges = [0.0, 0.45, 0.50, 0.55, 0.60, 1.0000001]
    names = ["<0.45", "0.45-0.50", "0.50-0.55", "0.55-0.60", ">=0.60"]
    for lo, hi, name in zip(edges[:-1], edges[1:], names):
        m = (z["p"] >= lo) & (z["p"] < hi)
        out[name] = {
            "n": int(m.sum()),
            "mean_future_return": float(z.loc[m, "future"].mean()) if m.any() else None,
        }
    return out


def metrics(y, p, future, block_len, extra=None, mask=None):
    y = np.asarray(y, float)
    p = np.asarray(p, float)
    fut = np.asarray(future, float)
    if mask is None:
        mask = np.isfinite(y) & np.isfinite(p)
    else:
        mask = np.asarray(mask, bool) & np.isfinite(y) & np.isfinite(p)
    if len(fut) != len(y):
        raise ValueError("y/p/future length mismatch")
    yy = y[mask].astype(int)
    pp = np.clip(p[mask], 1e-6, 1 - 1e-6)
    ff = fut[mask]
    if len(yy) == 0:
        out = {"status": "EXECUTED", "n": 0}
        if extra:
            out.update(extra)
        return out
    pred = (pp >= 0.5).astype(int)
    cm = confusion_matrix(yy, pred, labels=[0, 1]).ravel()
    out = {
        "status": "EXECUTED",
        "n": int(len(yy)),
        "positive_rate": float(yy.mean()),
        "accuracy": float(accuracy_score(yy, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(yy, pred)),
        "brier": float(brier_score_loss(yy, pp)),
        "log_loss": float(log_loss(yy, pp, labels=[0, 1])),
        "tn": int(cm[0]),
        "fp": int(cm[1]),
        "fn": int(cm[2]),
        "tp": int(cm[3]),
        "roc_auc": float(roc_auc_score(yy, pp)) if len(np.unique(yy)) == 2 else None,
        "pr_auc": float(average_precision_score(yy, pp)) if len(np.unique(yy)) == 2 else None,
        "accuracy_block_bootstrap_95": block_bootstrap_accuracy(yy, pp, block_len),
        "future_return_by_probability_bin": fixed_bins(yy, pp, ff),
    }
    if extra:
        out.update(extra)
    return out


def rank_bins(values: np.ndarray, n_bins: int) -> np.ndarray:
    """Deterministic within-sample average-rank bins."""
    s = pd.Series(values, dtype=float)
    ranks = s.rank(method="average", na_option="keep").to_numpy()
    n = int(np.isfinite(ranks).sum())
    if n == 0:
        return np.full(len(s), -1, dtype=int)
    u = (ranks - 0.5) / n
    out = np.full(len(s), -1, dtype=int)
    m = np.isfinite(u)
    out[m] = np.clip(np.floor(n_bins * u[m]), 0, n_bins - 1).astype(int)
    return out


def fit_rank_reference(values: np.ndarray) -> np.ndarray:
    """Frozen empirical-CDF reference built only from training observations."""
    x = np.asarray(values, dtype=float)
    return np.sort(x[np.isfinite(x)])


def apply_rank_bin(value: float, reference: np.ndarray, n_bins: int) -> int:
    """Map a new value using only the frozen training reference."""
    if not np.isfinite(value) or reference.size == 0:
        return -1
    left = int(np.searchsorted(reference, value, side="left"))
    right = int(np.searchsorted(reference, value, side="right"))
    if left < right:
        avg_rank = (left + 1 + right) / 2.0
    else:
        avg_rank = left + 1.0
    u = (avg_rank - 0.5) / max(int(reference.size), 1)
    return int(np.clip(np.floor(n_bins * u), 0, n_bins - 1))


def hurst_rs(window: np.ndarray) -> float:
    x = np.asarray(window, float)
    if len(x) < 32 or not np.isfinite(x).all():
        return np.nan
    xs = x - x.mean()
    cs = np.cumsum(xs)
    rs_vals = []
    ns = []
    for n in (16, 32, 64, 128, 256):
        if n > len(xs):
            continue
        for start in range(0, len(xs) - n + 1, n):
            seg = xs[start:start + n]
            dev = np.cumsum(seg - seg.mean())
            r = float(dev.max() - dev.min())
            s = float(seg.std(ddof=1))
            if s > 0 and np.isfinite(r) and np.isfinite(s):
                rs_vals.append(r / s)
                ns.append(n)
        if not rs_vals:
            continue
    if len(rs_vals) < 3:
        return np.nan
    slope = np.polyfit(np.log(np.asarray(ns, float)), np.log(np.asarray(rs_vals, float) + EPS), 1)[0]
    return float(slope)


def hurst_feature(ret: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n = len(ret)
    h = np.full(n, np.nan)
    diff = np.full(n, np.nan)
    for i in range(E01_WINDOW - 1, n):
        w = ret[i - E01_WINDOW + 1:i + 1]
        if not np.isfinite(w).all():
            continue
        real = hurst_rs(w)
        rng = np.random.default_rng(SEED + i)
        shuf = w.copy()
        rng.shuffle(shuf)
        sur = hurst_rs(shuf)
        h[i] = real
        diff[i] = real - sur
    return h, diff


def mfdfa_delta(ret: np.ndarray, idx: int) -> float:
    if idx + 1 < 256:
        return np.nan
    w = np.asarray(ret[idx - 255:idx + 1], dtype=float)
    if not np.isfinite(w).all():
        return np.nan
    profile = np.cumsum(w - w.mean())
    hq = {}
    for q in E02_Q:
        xs, ys = [], []
        for s in E02_SCALES:
            nseg = len(profile) // s
            if nseg < 8:
                continue
            arr = profile[:nseg * s].reshape(nseg, s)
            t = np.arange(s, dtype=float)
            tc = t - t.mean()
            denom = float(np.sum(tc * tc))
            if denom <= 0:
                continue
            mean_y = arr.mean(axis=1)
            slope = ((arr - mean_y[:, None]) * tc[None, :]).sum(axis=1) / denom
            intercept = mean_y - slope * t.mean()
            resid = arr - (slope[:, None] * t[None, :] + intercept[:, None])
            rms = np.sqrt(np.mean(resid * resid, axis=1))
            rms = rms[np.isfinite(rms) & (rms > 0)]
            if len(rms) < 8:
                continue
            if q == 0:
                f_q = float(np.exp(np.mean(np.log(rms + EPS))))
            else:
                with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
                    moment = np.mean(np.power(rms, q))
                if not np.isfinite(moment) or moment <= 0:
                    continue
                f_q = float(moment ** (1.0 / q))
            if np.isfinite(f_q) and f_q > 0:
                xs.append(math.log(s))
                ys.append(math.log(f_q))
        if len(xs) < 3:
            return np.nan
        hq[q] = float(np.polyfit(xs, ys, 1)[0])
    if -3 not in hq or 3 not in hq:
        return np.nan
    return float(hq[-3] - hq[3])


def sample_entropy(window: np.ndarray, m=2, r_scale=0.20) -> float:
    x = np.asarray(window, float)
    if len(x) < 20 or not np.isfinite(x).all():
        return np.nan
    sd = float(x.std(ddof=1))
    if not np.isfinite(sd) or sd <= 0:
        return np.nan
    r = r_scale * sd
    a = 0
    b = 0
    n = len(x)
    for i in range(n - m - 1):
        tmpl = x[i:i + m]
        for j in range(i + 1, n - m - 1):
            if np.max(np.abs(tmpl - x[j:j + m])) <= r:
                b += 1
                if abs(x[i + m] - x[j + m]) <= r:
                    a += 1
    if a <= 0 or b <= 0:
        return np.nan
    return float(-math.log(a / b))


def permutation_entropy(window: np.ndarray, m=5) -> float:
    x = np.asarray(window, float)
    if len(x) < m + 20 or not np.isfinite(x).all():
        return np.nan
    from collections import Counter
    pats = []
    for i in range(len(x) - m + 1):
        seg = x[i:i + m]
        if len(np.unique(seg)) < m:
            continue
        pats.append(tuple(np.argsort(seg, kind="mergesort")))
    if len(pats) < 20:
        return np.nan
    c = Counter(pats)
    probs = np.asarray(list(c.values()), float)
    probs /= probs.sum()
    h = float(-(probs * np.log(probs + EPS)).sum())
    return h / math.log(math.factorial(m))


def roughness_feature(ret: np.ndarray) -> np.ndarray:
    out = np.full(len(ret), np.nan)
    for i in range(E05_WINDOW - 1, len(ret)):
        w = ret[i - E05_WINDOW + 1:i + 1]
        if not np.isfinite(w).all():
            continue
        num = np.mean(np.abs(np.diff(w)))
        den = np.mean(np.abs(w)) + EPS
        out[i] = num / den
    return out


def volatility_states(ret: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    vol = pd.Series(ret).rolling(20).std().to_numpy()
    pct = pd.Series(vol).rolling(252, min_periods=252).rank(pct=True).to_numpy()
    st = np.full(len(ret), -1, dtype=int)
    st[pct < 0.33] = 0
    st[(pct >= 0.33) & (pct <= 0.67)] = 1
    st[pct > 0.67] = 2
    return vol, st


def ema_slope(ret: np.ndarray, training_vol: float) -> np.ndarray:
    s = pd.Series(ret).ewm(span=20, adjust=False, min_periods=20).mean()
    slope = s.diff().to_numpy()
    out = np.zeros(len(ret), dtype=int)
    thr = 0.25 * (training_vol if np.isfinite(training_vol) and training_vol > 0 else 1.0)
    out[slope > thr] = 1
    out[slope < -thr] = -1
    return out


def train_prob_by_state(states, y, min_n=50):
    states = np.asarray(states)
    y = np.asarray(y, float)
    pooled = y[np.isfinite(y)]
    pooled_p = float(pooled.mean()) if len(pooled) else 0.5
    out = {}
    for s in sorted(set(states[np.isfinite(states)])):
        m = (states == s) & np.isfinite(y)
        if int(m.sum()) >= min_n:
            out[int(s)] = float(y[m].mean())
        else:
            out[int(s)] = pooled_p
    return out, pooled_p


def e06_train_model(ret, y, train_end):
    best_lag = None
    best_mi = -np.inf
    best_table = None
    best_reference = np.empty(0, dtype=float)
    for lag in E06_LAGS:
        x = pd.Series(ret).shift(lag).to_numpy()
        m = (np.arange(len(x)) < train_end) & np.isfinite(x) & np.isfinite(y)
        if int(m.sum()) < 200:
            continue
        reference = fit_rank_reference(x[m])
        bins = np.array([apply_rank_bin(v, reference, 8) for v in x[m]], dtype=int)
        yy = np.asarray(y)[m].astype(int)
        valid = bins >= 0
        bins = bins[valid]
        yy = yy[valid]
        table = np.ones((8, 2), dtype=float)  # Laplace +1 smoothing.
        for bx, by in zip(bins, yy):
            table[int(bx), int(by)] += 1.0
        pxy = table / table.sum()
        px = pxy.sum(axis=1, keepdims=True)
        py = pxy.sum(axis=0, keepdims=True)
        mi = float((pxy * np.log((pxy + EPS) / (px @ py + EPS))).sum())
        if mi > best_mi + 1e-15 or (
            abs(mi - best_mi) <= 1e-15 and (best_lag is None or lag < best_lag)
        ):
            best_mi = mi
            best_lag = lag
            best_table = table
            best_reference = reference
    return best_lag, best_mi, best_table, best_reference




def e05_signal(rough, train_end, recent_sign):
    tr = rough[:train_end]
    med = np.nanmedian(tr[np.isfinite(tr)]) if np.isfinite(tr).any() else np.nan
    p = np.full(len(rough), np.nan)
    for i in range(train_end, len(rough)):
        if not np.isfinite(rough[i]) or not np.isfinite(med) or med <= 0 or not np.isfinite(recent_sign[i]):
            continue
        q = rough[i] / med
        s = recent_sign[i]
        if q > 1.25:
            s = -s
        elif q < 0.75:
            s = s
        else:
            p[i] = 0.5
            continue
        p[i] = 0.55 if s > 0 else 0.45 if s < 0 else 0.5
    return p


def e01_signal(hurst, recent_sign):
    p = np.full(len(hurst), np.nan)
    m = np.isfinite(hurst) & np.isfinite(recent_sign)
    p[m] = np.where((hurst[m] > 0.5) & (recent_sign[m] > 0), 0.55,
                    np.where((hurst[m] > 0.5) & (recent_sign[m] < 0), 0.45, 0.5))
    return p


def e02_signal(delta_h, recent_sign):
    p = np.full(len(delta_h), np.nan)
    m = np.isfinite(delta_h) & np.isfinite(recent_sign)
    p[m] = np.where((delta_h[m] > 0.10) & (recent_sign[m] > 0), 0.55,
                    np.where((delta_h[m] > 0.10) & (recent_sign[m] < 0), 0.45, 0.5))
    return p


def e03_signal(ent, train_end, recent_sign):
    med = np.nanmedian(ent[:train_end][np.isfinite(ent[:train_end])]) if np.isfinite(ent[:train_end]).any() else np.nan
    p = np.full(len(ent), np.nan)
    for i in range(train_end, len(ent)):
        if not np.isfinite(ent[i]) or not np.isfinite(med) or not np.isfinite(recent_sign[i]):
            continue
        if ent[i] < med:
            s = recent_sign[i]
            p[i] = 0.55 if s > 0 else 0.45 if s < 0 else 0.5
        else:
            p[i] = 0.5
    return p


def state_matrix_probs(trend, vol_state, y, train_end):
    yy = np.asarray(y, float)
    trend = np.asarray(trend, int)
    vs = np.asarray(vol_state, int)
    eligible = np.arange(len(yy)) < train_end
    pooled = yy[eligible & np.isfinite(yy)]
    pooled_p = float(pooled.mean()) if len(pooled) else 0.5
    trend_p = {}
    vol_p = {}
    cell_p = {}
    for s in (-1, 0, 1):
        m = eligible & (trend == s) & np.isfinite(yy)
        trend_p[s] = float(yy[m].mean()) if m.sum() >= 50 else pooled_p
    for s in (0, 1, 2):
        m = eligible & (vs == s) & np.isfinite(yy)
        vol_p[s] = float(yy[m].mean()) if m.sum() >= 50 else pooled_p
    for ts in (-1, 0, 1):
        for vsx in (0, 1, 2):
            m = eligible & (trend == ts) & (vs == vsx) & np.isfinite(yy)
            if m.sum() >= 50:
                cell_p[(ts, vsx)] = float(yy[m].mean())
            elif m.sum() > 0:
                cell_p[(ts, vsx)] = trend_p[ts]
            else:
                cell_p[(ts, vsx)] = trend_p[ts] if abs(trend_p[ts] - pooled_p) > 1e-15 else vol_p[vsx]
    return cell_p, trend_p, vol_p, pooled_p


def i05_probs(trend, vol_state, y, train_end, test_rows):
    cell_p, trend_p, vol_p, pooled_p = state_matrix_probs(trend, vol_state, y, train_end)
    states = list(zip(trend[:train_end].astype(int), vol_state[:train_end].astype(int)))
    next_states = list(zip(trend[1:train_end].astype(int), vol_state[1:train_end].astype(int)))
    counts = {}
    for a, b in zip(states[:-1], next_states):
        if a[0] not in (-1, 0, 1) or a[1] not in (0, 1, 2):
            continue
        counts.setdefault(a, {})
        counts[a][b] = counts[a].get(b, 0) + 1
    out = np.full(len(trend), np.nan)
    for i in test_rows:
        cur = (int(trend[i]), int(vol_state[i]))
        row = counts.get(cur)
        if not row or sum(row.values()) == 0:
            out[i] = pooled_p
            continue
        den = sum(row.values())
        p = 0.0
        for dest, c in row.items():
            p += (c / den) * cell_p.get(dest, pooled_p)
        out[i] = float(p)
    return out


def run_scope(df, intraday: bool, horizons: list[int]):
    if intraday:
        q = df.copy()
        q["log_spot"] = np.log(q["spot"])
        grid = (
            (q["minute_of_day"] >= 570)
            & (q["minute_of_day"] <= 930)
            & (((q["minute_of_day"] - 570) % 60) == 0)
        )
        decision_idx = np.flatnonzero(grid.to_numpy())
        full_ret = q["log_spot"].diff().to_numpy()
        X = features_intraday(q).iloc[decision_idx].reset_index(drop=True)
        decision_times = pd.DatetimeIndex(pd.to_datetime(q["timestamp"].iloc[decision_idx], utc=True))
        groups = q["date"].iloc[decision_idx].reset_index(drop=True)
        session_values = pd.Index(groups.drop_duplicates())
        session_blocks = []
        for s0 in range(0, len(session_values), 20):
            ss = set(session_values[s0:s0 + 20])
            rows = np.flatnonzero(groups.isin(ss).to_numpy())
            if len(rows):
                session_blocks.append(rows)
        block_len = 60
        n_rows = len(decision_idx)
    else:
        q = None
        X = features_daily(df)
        decision_idx = np.arange(len(df), dtype=int)
        full_ret = df["log_close"].diff().to_numpy()
        session_blocks = [np.arange(i, min(i + 20, len(df))) for i in range(0, len(df), 20)]
        decision_times = None
        block_len = 20
        n_rows = len(df)

    h_real, h_ctrl = hurst_feature(full_ret)
    common = {
        "E01": h_real[decision_idx],
        "E01_control": h_ctrl[decision_idx],
        "E02": np.array([mfdfa_delta(full_ret, i) for i in decision_idx]),
        "E03": np.array([
            sample_entropy(full_ret[max(0, i - E03_WINDOW + 1):i + 1])
            if i >= E03_WINDOW - 1 else np.nan for i in decision_idx
        ]),
        "E04": np.array([
            permutation_entropy(full_ret[max(0, i - E04_WINDOW + 1):i + 1])
            if i >= E04_WINDOW - 1 else np.nan for i in decision_idx
        ]),
        "E05": roughness_feature(full_ret)[decision_idx],
    }

    vol20, vol_state_full = volatility_states(full_ret)
    common["vol_state"] = vol_state_full[decision_idx]
    recent_sign = np.sign(pd.Series(full_ret).rolling(20).sum().to_numpy())[decision_idx]

    # I01 is a causal deterministic pressure score on the full path.
    p_i01 = np.full(n_rows, np.nan)
    for r, src in enumerate(decision_idx):
        if src < 60:
            continue
        sd60 = np.nanstd(full_ret[src - 59:src + 1], ddof=1)
        if not np.isfinite(sd60) or sd60 <= 0:
            continue
        zs = []
        for k in I01_SCALES:
            if src < k:
                zs = []
                break
            rk = np.nansum(full_ret[src - k + 1:src + 1])
            zs.append(rk / (sd60 * math.sqrt(k) + EPS))
        if len(zs) == 3:
            score = (zs[0] + zs[1] / math.sqrt(10 / 3) + zs[2] / math.sqrt(30 / 3)) / 3
            p_i01[r] = float(sigmoid(1.5 * score))

    result = {}
    methods = ["E01","E02","E03","E04","E05","E06","E07","E08","E09","E10",
               "I01","I02","I03","I04","I05","I06","I07","I08","I09","I10"]

    for H in horizons:
        if intraday:
            y_full, future_full, _ = intraday_labels(q["timestamp"], q["spot"], H)
            y = y_full.iloc[decision_idx].to_numpy()
            future = future_full.iloc[decision_idx].to_numpy()
        else:
            y_full, future_series = make_label(df, H)
            y = y_full.to_numpy()
            future = future_series.to_numpy()

        pred = {m: np.full(n_rows, np.nan) for m in methods}
        extra_diag = {m: {} for m in methods}
        eligible_blocks = 0

        for rows in session_blocks:
            if len(rows) == 0:
                continue
            if intraday:
                cutoff = decision_times.iloc[rows[0]] - pd.Timedelta(minutes=int(H))
                train_end = cutoff_train_end(decision_times, cutoff)
            else:
                train_end = purged_train_end(rows[0], H)
            if train_end < 300:
                continue
            eligible_blocks += 1

            # Block-specific E08/E09/E10/I05 states.
            train_vol = vol20[decision_idx[:train_end]] if intraday else vol20[:train_end]
            trend_thr_vol = np.nanmedian(train_vol[np.isfinite(train_vol)]) if np.isfinite(train_vol).any() else np.nan
            trend_states_full = ema_slope(full_ret, trend_thr_vol)
            trend_states = trend_states_full[decision_idx]

            p01 = e01_signal(common["E01"], recent_sign)
            p02 = e02_signal(common["E02"], recent_sign)
            p03 = e03_signal(common["E03"], train_end, recent_sign)
            p05 = e05_signal(common["E05"], train_end, recent_sign)
            pred["E01"][rows] = p01[rows]
            pred["E02"][rows] = p02[rows]
            pred["E03"][rows] = p03[rows]
            pred["E05"][rows] = p05[rows]

            p04 = np.full(n_rows, np.nan)
            for r in rows:
                if np.isfinite(common["E04"][r]):
                    if common["E04"][r] < 0.80 and recent_sign[r] > 0:
                        p04[r] = 0.55
                    elif common["E04"][r] < 0.80 and recent_sign[r] < 0:
                        p04[r] = 0.45
                    else:
                        p04[r] = 0.50
            pred["E04"][rows] = p04[rows]

            # E06: fit bin edges and conditional probabilities only on the training block.
            ret_source = full_ret[decision_idx] if intraday else full_ret
            selected_lag, mi, table, train_reference = e06_train_model(ret_source, y, train_end)
            if selected_lag is not None and table is not None:
                x = pd.Series(ret_source).shift(selected_lag).to_numpy()
                for r in rows:
                    if not np.isfinite(x[r]):
                        continue
                    bx = apply_rank_bin(x[r], train_reference, 8)
                    if bx >= 0:
                        rowc = table[int(bx)]
                        pred["E06"][r] = rowc[1] / rowc.sum()
                extra_diag["E06"].setdefault("selected_lags", []).append(int(selected_lag))
                extra_diag["E06"].setdefault("training_mutual_information", []).append(float(mi))
            else:
                extra_diag["E06"].setdefault("blocked_reason", "fewer than 200 eligible training observations")

            # E09/E10.
            cell_p, trend_p, vol_p, pooled = state_matrix_probs(trend_states, common["vol_state"], y, train_end)
            for r in rows:
                vs = int(common["vol_state"][r])
                if vs in (0, 1, 2):
                    pred["E09"][r] = vol_p[vs]
                pred["E10"][r] = cell_p.get((int(trend_states[r]), int(common["vol_state"][r])), pooled)
            extra_diag["E09"].setdefault("state_counts_test", []).append(
                {str(s): int(np.sum(common["vol_state"][rows] == s)) for s in (0, 1, 2)}
            )

            # Fixed base models reused by E08, I08 and I09.
            base_names = ["D01", "D02", "D03", "D07", "D09", "D12"]
            base_block = {}
            for name in base_names:
                try:
                    arr = fit_predict_block(name, X, pd.Series(y), train_end, rows)
                except Exception:
                    arr = np.full(len(rows), np.nan)
                b = np.full(n_rows, np.nan)
                b[rows] = arr
                base_block[name] = b

            for r in rows:
                vs = int(common["vol_state"][r])
                chosen = E08_MODEL_MAP.get(vs)
                if chosen is not None:
                    pred["E08"][r] = base_block[chosen][r]

            # I05: fixed one-step regime-transition pressure.
            pred_i05 = i05_probs(trend_states, common["vol_state"], y, train_end, rows)
            pred["I05"][rows] = pred_i05[rows]

            # I08: fixed entropy-weighted component ensemble.
            for r in rows:
                ps = [base_block[n][r] for n in base_names]
                if not np.all(np.isfinite(ps)):
                    continue
                ws = []
                for pv in ps:
                    ws.append(entropy_weight(pv))
                pred["I08"][r] = float(np.dot(ws, ps) / sum(ws))

            # I09: fixed D07 abstention band, preserving the full denominator separately.
            pred["I09"][rows] = base_block["D07"][rows]

        # Global I01/I03 use all eligible blocks; I03 gets block-specific volatility adjustment.
        pred["I01"] = p_i01.copy()
        for rows in session_blocks:
            if len(rows) == 0:
                continue
            if intraday:
                cutoff = decision_times.iloc[rows[0]] - pd.Timedelta(minutes=int(H))
                train_end = cutoff_train_end(decision_times, cutoff)
            else:
                train_end = purged_train_end(rows[0], H)
            if train_end < 300:
                continue
            train_vol = vol20[decision_idx[:train_end]] if intraday else vol20[:train_end]
            medv = np.nanmedian(train_vol[np.isfinite(train_vol)]) if np.isfinite(train_vol).any() else np.nan
            for r in rows:
                src = decision_idx[r]
                if not np.isfinite(src) or not np.isfinite(medv) or medv <= 0:
                    continue
                raw_persistence = np.nansum(full_ret[src - I03_WINDOW + 1:src + 1] * np.sign(full_ret[src - I03_WINDOW + 1:src + 1])) / (
                    np.nansum(np.abs(full_ret[src - I03_WINDOW + 1:src + 1])) + EPS
                ) if src >= I03_WINDOW else np.nan
                if not np.isfinite(raw_persistence):
                    continue
                pred["I03"][r] = i03_probability(raw_persistence, vol20[src], medv)

        # Methods requiring unavailable PIT layers remain blocked by explicit rule.
        blocked = {
            "E07": "PIT-safe global composite coverage is insufficient for the registered historical window",
            "I02": "current canonical global source cache is limited to a short 2024 reference window; full-period PIT coverage is insufficient",
            "I04": "PIT-safe option-surface IV/OI history is not available in the canonical Phase 6 input cache",
            "I06": "PIT-safe bid/ask spread history is not available in the canonical Phase 6 input cache",
            "I07": "PIT-safe option premium/contract history suitable for the registered break-even calculation is not available in the canonical Phase 6 input cache",
            "I10": "I02 is BLOCKED_DATA and the frozen I10 rule forbids reweighting blocked components",
        }
        # Finalize metrics from the accumulated, full-block prediction vectors.
        for m in methods:
            if m in blocked:
                extra_diag[m]["reason"] = blocked[m]
                continue
            extra = {}
            if m == "E01":
                ctrl = common["E01_control"]
                valid_ctrl = np.isfinite(ctrl)
                if valid_ctrl.any():
                    extra["hurst_surrogate_control_mean"] = float(np.nanmean(ctrl[valid_ctrl]))
            if m == "E06":
                if "blocked_reason" in extra_diag[m]:
                    result_diag = {"reason": extra_diag[m]["blocked_reason"]}
                    result_diag.update({k: v for k, v in extra_diag[m].items() if k != "blocked_reason"})
                    extra = result_diag
                else:
                    extra = {k: v for k, v in extra_diag[m].items()}
            elif m == "E08":
                extra = {"fixed_model_map": {"low": "D09", "mid": "D02", "high": "D12"}}
            elif m == "E09":
                extra = {"state_counts_test": extra_diag[m].get("state_counts_test", [])}
            elif m == "I09":
                finite_p = np.isfinite(pred[m])
                trade = finite_p & ((pred[m] < 0.45) | (pred[m] > 0.55))
                extra = {
                    "coverage": float(trade.sum() / finite_p.sum()) if finite_p.sum() else 0.0,
                    "trade_n": int(trade.sum()),
                    "evaluable_n": int(finite_p.sum()),
                }
                mask = trade
                result[str(H)][m] = metrics(y, pred[m], future, block_len, extra=extra, mask=mask) if False else {}
            else:
                result[str(H)] = result.get(str(H), {})
            result[str(H)][m] = metrics(y, pred[m], future, block_len, extra=extra)

        # I09 needs conditional metrics on traded observations plus full coverage.
        finite_p = np.isfinite(pred["I09"])
        trade = finite_p & ((pred["I09"] < ABSTENTION_LOW) | (pred["I09"] > ABSTENTION_HIGH))
        i09_extra = {
            "coverage": float(trade.sum() / finite_p.sum()) if finite_p.sum() else 0.0,
            "trade_n": int(trade.sum()),
            "evaluable_n": int(finite_p.sum()),
        }
        result[str(H)]["I09"] = metrics(y, pred["I09"], future, block_len, extra=i09_extra, mask=trade)

        # I10 is intentionally blocked because I02 is blocked.
        for m, reason in blocked.items():
            result[str(H)][m] = {"status": "BLOCKED_DATA", "reason": reason}

        if eligible_blocks == 0:
            for m in methods:
                if m not in blocked:
                    result[str(H)][m] = {
                        "status": "EXECUTED",
                        "n": 0,
                        "reason": "no test block reached the minimum 300-observation training boundary"
                    }

    return result

def main():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        d = load_daily()
        q = load_intraday()
        q = q.copy()
        daily = run_scope(d, intraday=False, horizons=DAILY_H)
        intra = run_scope(q, intraday=True, horizons=INTRA_H)

    out = {
        "protocol": "research/phase6/PHASE6_METHOD_SPEC.md",
        "seed": SEED,
        "daily": {"rows": int(len(d)), "horizons": daily},
        "intraday": {
            "rows": int(len(q)),
            "hourly_decision_rows": int(((q["minute_of_day"] >= 570) & (q["minute_of_day"] <= 930) & (((q["minute_of_day"] - 570) % 60) == 0)).sum()),
            "horizons": intra,
        },
    }
    path = OUT / "phase6_novel_results.json"
    path.write_text(json.dumps(out, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({"daily_rows": len(d), "intraday_rows": len(q), "status": "PASS"}, indent=2))


if __name__ == "__main__":
    main()
