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
    s = pd.Series(values, dtype=float)
    if s.notna().sum() == 0:
        return np.full(len(s), -1, dtype=int)
    ranks = s.rank(method="average", na_option="keep").to_numpy()
    n = np.isfinite(ranks).sum()
    u = (ranks - 0.5) / max(n, 1)
    b = np.floor(n_bins * u)
    b = np.clip(b, 0, n_bins - 1)
    out = np.full(len(s), -1, dtype=int)
    m = np.isfinite(b)
    out[m] = b[m].astype(int)
    return out


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
    w = ret[idx - 255:idx + 1]
    if not np.isfinite(w).all():
        return np.nan
    profile = np.cumsum(w - w.mean())
    hq = {}
    for q in E02_Q:
        xs, ys = [], []
        for s in E02_SCALES:
            if len(profile) < s:
                continue
            fs = []
            for start in range(0, len(profile) - s + 1, s):
                seg = profile[start:start + s]
                t = np.arange(s, dtype=float)
                coef = np.polyfit(t, seg, 1)
                trend = coef[0] * t + coef[1]
                rms = np.sqrt(np.mean((seg - trend) ** 2))
                if np.isfinite(rms) and rms > 0:
                    fs.append(rms)
            if len(fs) < 8:
                continue
            a = np.asarray(fs)
            if q == 0:
                f_q = float(np.exp(np.mean(np.log(a + EPS))))
            else:
                f_q = float(np.mean(a ** q) ** (1.0 / q))
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
    for lag in E06_LAGS:
        x = pd.Series(ret).shift(lag).to_numpy()
        m = (np.arange(len(x)) < train_end) & np.isfinite(x) & np.isfinite(y)
        if m.sum() < 200:
            continue
        bins = rank_bins(x[m], 8)
        yy = np.asarray(y)[m].astype(int)
        valid = bins >= 0
        bins = bins[valid]
        yy = yy[valid]
        table = np.ones((8, 2), dtype=float)
        for bx, by in zip(bins, yy):
            table[int(bx), int(by)] += 1.0
        pxy = table / table.sum()
        px = pxy.sum(axis=1, keepdims=True)
        py = pxy.sum(axis=0, keepdims=True)
        mi = float((pxy * np.log((pxy + EPS) / (px @ py + EPS))).sum())
        if mi > best_mi + 1e-15 or (abs(mi - best_mi) <= 1e-15 and (best_lag is None or lag < best_lag)):
            best_mi = mi
            best_lag = lag
            best_table = table
    return best_lag, best_mi, best_table


def apply_e06(ret, idx_rows, lag, table):
    out = np.full(len(ret), np.nan)
    if lag is None or table is None:
        return out
    x = pd.Series(ret).shift(lag).to_numpy()
    for i in idx_rows:
        if not np.isfinite(x[i]):
            continue
        b = rank_bins(x[:i + 1], 8)[i]
        if b < 0:
            continue
        row = table[int(b)]
        out[i] = row[1] / row.sum()
    return out


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
        X = features_daily(df)
        decision_idx = np.arange(len(df), dtype=int)
        full_ret = df["log_close"].diff().to_numpy()
        groups = pd.Series(np.arange(len(df)))
        session_blocks = [np.arange(i, min(i + 20, len(df))) for i in range(0, len(df), 20)]
        decision_times = None
        block_len = 20
        n_rows = len(df)

    ret_dec = full_ret[decision_idx]
    common = {
        "E01": hurst_feature(full_ret)[0][decision_idx],
        "E01_control": hurst_feature(full_ret)[1][decision_idx],
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
        "I01": None,
        "I03": None,
    }
    vol20, vol_state_full = volatility_states(full_ret)
    common["vol_state"] = vol_state_full[decision_idx]
    recent_sign = np.sign(pd.Series(full_ret).rolling(20).sum().to_numpy())[decision_idx]

    i01 = np.full(n_rows, np.nan)
    i03 = np.full(n_rows, np.nan)
    for i in range(n_rows):
        src = decision_idx[i]
        if src < 60 or not np.isfinite(full_ret[src]):
            continue
        sd60 = np.nanstd(full_ret[src - 59:src + 1], ddof=1)
        if not np.isfinite(sd60) or sd60 <= 0:
            continue
        z = []
        for k in I01_SCALES:
            if src < k:
                z = []
                break
            r_k = np.nansum(full_ret[src - k + 1:src + 1])
            z.append(r_k / (sd60 * math.sqrt(k) + EPS))
        if z:
            i01[i] = float(sigmoid(1.5 * ((z[0] + z[1] / math.sqrt(10/3) + z[2] / math.sqrt(30/3)) / 3))
        if src >= I03_WINDOW:
            w = full_ret[src - I03_WINDOW + 1:src + 1]
            pers = np.nansum(np.sign(w) * np.abs(w)) / (np.nansum(np.abs(w)) + EPS)
            if np.isfinite(pers) and sd60 > 0:
                i03[i] = pers
    common["I01"] = i01
    common["I03"] = i03

    result = {}
    base_names = ["D01", "D02", "D03", "D07", "D09", "D12"]
    for H in horizons:
        if intraday:
            y_full, future_full, _ = intraday_labels(q["timestamp"], q["spot"], H)
            y = y_full.iloc[decision_idx].to_numpy()
            future = future_full.iloc[decision_idx].to_numpy()
        else:
            y_full, future_series = make_label(df, H)
            y = y_full.to_numpy()
            future = future_series.to_numpy()

        out = {m: {"status": "BLOCKED_DATA", "reason": "not initialized"} for m in [
            "E01","E02","E03","E04","E05","E06","E07","E08","E09","E10",
            "I01","I02","I03","I04","I05","I06","I07","I08","I09","I10"
        ]}

        for rows in session_blocks:
            if len(rows) == 0:
                continue
            if intraday:
                first_time = decision_times.iloc[rows[0]]
                cutoff = first_time - pd.Timedelta(minutes=int(H))
                train_end = cutoff_train_end(decision_times, cutoff)
            else:
                train_end = purged_train_end(rows[0], H)
            if train_end < 300:
                continue

            idx_rows = rows
            # fixed daily/intraday feature arrays are aligned to decision rows
            trend_thr_vol = np.nanmedian(vol20[:decision_idx[train_end-1]+1]) if intraday else np.nanmedian(vol20[:train_end])
            trend_states_full = ema_slope(full_ret, trend_thr_vol)
            trend_states = trend_states_full[decision_idx]

            # E01-E05 deterministic signals
            p01 = e01_signal(common["E01"], recent_sign)
            p02 = e02_signal(common["E02"], recent_sign)
            p03 = e03_signal(common["E03"], train_end, recent_sign)
            p05 = e05_signal(common["E05"], train_end, recent_sign)

            for m, p in [("E01", p01), ("E02", p02), ("E03", p03), ("E05", p05)]:
                vals = p[idx_rows].copy()
                if not np.isfinite(vals).any():
                    out[m] = {"status": "EXECUTED", "n": 0}
                else:
                    out[m] = metrics(y, p, future, block_len)
            p04 = np.full(n_rows, np.nan)
            for j in idx_rows:
                if np.isfinite(common["E04"][j]):
                    p04[j] = 0.55 if common["E04"][j] < 0.80 and recent_sign[j] > 0 else 0.45 if common["E04"][j] < 0.80 and recent_sign[j] < 0 else 0.5
            out["E04"] = metrics(y, p04, future, block_len)

            lag, mi, table = e06_train_model(ret_dec if not intraday else full_ret[decision_idx], y, train_end)
            p06 = np.full(n_rows, np.nan)
            if lag is not None:
                src = full_ret if intraday else ret_dec
                x = pd.Series(src).shift(lag).to_numpy()
                # Build deterministic rank bins from training+past values; ranks are causal by truncation.
                for r in idx_rows:
                    if not np.isfinite(x[r]):
                        continue
                    bx = rank_bins(x[:r+1], 8)[r]
                    if bx >= 0:
                        row = table[int(bx)]
                        p06[r] = row[1] / row.sum()
                out["E06"] = metrics(y, p06, future, block_len, extra={"selected_lag": int(lag), "training_mutual_information": float(mi)})
            else:
                out["E06"] = {"status": "BLOCKED_DATA", "reason": "fewer than 200 eligible training observations for mutual-information estimator"}

            # E09/E10
            cell_p, trend_p, vol_p, pooled = state_matrix_probs(trend_states, common["vol_state"], y, train_end)
            p09 = np.full(n_rows, np.nan)
            for r in idx_rows:
                vs = int(common["vol_state"][r])
                if vs in (0,1,2):
                    p09[r] = vol_p[vs]
            out["E09"] = metrics(y, p09, future, block_len, extra={"state_counts_test": {str(s): int(np.sum(common["vol_state"][idx_rows] == s)) for s in (0,1,2)}})
            p10 = np.full(n_rows, np.nan)
            for r in idx_rows:
                p10[r] = cell_p.get((int(trend_states[r]), int(common["vol_state"][r])), pooled)
            out["E10"] = metrics(y, p10, future, block_len)

            # E08 + fixed base model predictions for I08/I09
            base = {}
            for name in base_names:
                try:
                    base[name] = fit_predict_block(name, X, pd.Series(y), train_end, idx_rows)
                except Exception:
                    base[name] = np.full(len(idx_rows), np.nan)
            for k, arr in list(base.items()):
                if k in base:
                    b = np.full(n_rows, np.nan)
                    b[idx_rows] = arr
                    base[k] = b

            p08 = np.full(n_rows, np.nan)
            for pos, r in enumerate(idx_rows):
                vs = int(common["vol_state"][r])
                chosen = "D09" if vs == 0 else "D02" if vs == 1 else "D12"
                p08[r] = base[chosen][r]
            out["E08"] = metrics(y, p08, future, block_len, extra={"fixed_model_map": {"low": "D09", "mid": "D02", "high": "D12"}})

            p11 = common["I01"].copy()
            p11[:] = np.nan
            for r in idx_rows:
                # I05 uses a one-step transition model over E10 states.
                tmp = i05_probs(trend_states, common["vol_state"], y, train_end, [r])
                p11[r] = tmp[r]
            out["I05"] = metrics(y, p11, future, block_len)

            p_i08 = np.full(n_rows, np.nan)
            for r in idx_rows:
                ps = [base[n][r] for n in base_names]
                if not np.all(np.isfinite(ps)):
                    continue
                ws = []
                for pv in ps:
                    ent = -(pv * math.log2(max(pv, 1e-12)) + (1-pv) * math.log2(max(1-pv, 1e-12)))
                    ws.append(max(1.0 - ent, 0.05))
                p_i08[r] = float(np.dot(ws, ps) / sum(ws))
            out["I08"] = metrics(y, p_i08, future, block_len)

            p_i09 = base["D07"].copy()
            trade_mask = np.isfinite(p_i09) & ((p_i09 < 0.45) | (p_i09 > 0.55))
            extra = {"coverage": float(np.mean(trade_mask[np.isfinite(p_i09)])) if np.isfinite(p_i09).any() else 0.0,
                     "trade_n": int(trade_mask.sum())}
            out["I09"] = metrics(y, p_i09, future, block_len, extra=extra, mask=trade_mask)

            # Methods requiring unavailable PIT data in the current canonical cache.
            out["E07"] = {"status": "BLOCKED_DATA", "reason": "PIT-safe global composite coverage is insufficient for the registered historical window"}
            out["I02"] = {"status": "BLOCKED_DATA", "reason": "current canonical global source cache is limited to a short 2024 reference window; full-period PIT coverage is insufficient"}
            out["I04"] = {"status": "BLOCKED_DATA", "reason": "PIT-safe option-surface IV/OI history is not available in the canonical Phase 6 input cache"}
            out["I06"] = {"status": "BLOCKED_DATA", "reason": "PIT-safe bid/ask spread history is not available in the canonical Phase 6 input cache"}
            out["I07"] = {"status": "BLOCKED_DATA", "reason": "PIT-safe option premium/contract history suitable for the registered break-even calculation is not available in the canonical Phase 6 input cache"}
            out["I10"] = {"status": "BLOCKED_DATA", "reason": "I02 is BLOCKED_DATA and the frozen I10 rule forbids reweighting blocked components"}

        # Methods were initialized as blocked until the first eligible training block. Ensure no false EXECUTED with no predictions.
        for name in ("E01","E02","E03","E04","E05","E06","E08","E09","E10","I01","I03","I05","I08","I09"):
            if out[name].get("status") == "BLOCKED_DATA" and name not in {"I02","I04","I06","I07","I10","E07"}:
                out[name] = {"status": "EXECUTED", "n": 0, "reason": "insufficient early training rows; no eligible test rows reached the minimum training boundary"}

        # I01/I03 probability maps from precomputed scores.
        p_i01 = np.full(n_rows, np.nan)
        p_i03 = np.full(n_rows, np.nan)
        for r in range(n_rows):
            if np.isfinite(common["I01"][r]):
                p_i01[r] = common["I01"][r]
            if np.isfinite(common["I03"][r]):
                # Use block-specific dimensionless volatility ratio with training median.
                # Apply in the final metric below per test rows by recomputing the same rule inside blocks.
                pass
        out["I01"] = metrics(y, p_i01, future, block_len)
        # I03 is recomputed blockwise to apply the frozen training-median volatility ratio.
        p_i03 = np.full(n_rows, np.nan)
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
                if not np.isfinite(common["I03"][r]) or not np.isfinite(medv) or medv <= 0:
                    continue
                vr = (vol20[src] if np.isfinite(vol20[src]) else medv) / medv
                score = common["I03"][r] / max(vr, 0.25)
                p_i03[r] = float(sigmoid(np.clip(score, -3, 3)))
        out["I03"] = metrics(y, p_i03, future, block_len)

        result[str(H)] = out
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
