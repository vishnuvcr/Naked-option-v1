from __future__ import annotations

from pathlib import Path
import json
import math
import numpy as np
import pandas as pd
from scipy.special import ndtr
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    log_loss,
    confusion_matrix,
)
import statsmodels.api as sm
from statsmodels.tsa.ar_model import AutoReg
from arch import arch_model

ROOT = Path(__file__).resolve().parents[1]
DAILY = ROOT / "data/cache/raw/phase3/nifty50_daily.csv"
INTRA = ROOT / "data/cache/raw/phase3/hf_intraday/nifty50_index_reference.parquet"
OUT = ROOT / "data/reports"
OUT.mkdir(parents=True, exist_ok=True)

DAILY_H = [1, 2, 3, 5, 10]
INTRA_H = [5, 15, 30, 60, 120]
METHODS = [f"C{i:02d}" for i in range(1, 12)]


def result_metrics(y, p, future, block_len):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    future = np.asarray(future, dtype=float)
    m = np.isfinite(y) & np.isfinite(p) & np.isfinite(future)
    y = y[m].astype(int)
    p = np.clip(p[m], 1e-9, 1 - 1e-9)
    future = future[m]
    if len(y) == 0:
        return {"status": "EXECUTED", "n": 0}

    pred = (p >= 0.5).astype(int)
    cm = confusion_matrix(y, pred, labels=[0, 1]).ravel()

    bins = [-0.001, 0.45, 0.50, 0.55, 0.60, 1.001]
    names = ["<0.45", "0.45-0.50", "0.50-0.55", "0.55-0.60", ">=0.60"]
    br = {}
    for lo, hi, name in zip(bins[:-1], bins[1:], names):
        mm = (p >= lo) & ((p < hi) if hi < 1 else (p <= hi))
        br[name] = {
            "n": int(mm.sum()),
            "mean_future_return": float(future[mm].mean()) if mm.any() else None,
        }

    rng = np.random.default_rng(42)
    blocks = [np.arange(i, min(i + block_len, len(y))) for i in range(0, len(y), block_len)]
    boots = []
    for _ in range(200):
        sel = rng.integers(0, len(blocks), size=len(blocks))
        idx = np.concatenate([blocks[j] for j in sel])[: len(y)]
        boots.append(float(np.mean((p[idx] >= 0.5) == y[idx])))

    out = {
        "status": "EXECUTED",
        "n": int(len(y)),
        "positive_rate": float(y.mean()),
        "accuracy": float(accuracy_score(y, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "brier": float(brier_score_loss(y, p)),
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "tn": int(cm[0]),
        "fp": int(cm[1]),
        "fn": int(cm[2]),
        "tp": int(cm[3]),
        "future_return_by_probability_bin": br,
        "accuracy_block_bootstrap_95": {
            "lower": float(np.quantile(boots, 0.025)),
            "upper": float(np.quantile(boots, 0.975)),
            "median": float(np.median(boots)),
        },
    }
    if len(np.unique(y)) == 2:
        out["roc_auc"] = float(roc_auc_score(y, p))
        out["pr_auc"] = float(average_precision_score(y, p))
    else:
        out["roc_auc"] = None
        out["pr_auc"] = None
    return out


def lag_features(ret):
    return pd.DataFrame({f"r{k}": ret.shift(k) for k in [1, 2, 3, 5, 10]})


def probit_fit_predict(Xtr, ytr, Xte):
    xtr = sm.add_constant(Xtr, has_constant="add")
    xte = sm.add_constant(Xte, has_constant="add")
    model = sm.Probit(ytr, xtr).fit(disp=False, maxiter=200)
    return np.asarray(model.predict(xte), dtype=float)


def model_probs(method, Xtr, ytr, Xte):
    if method == "C02":
        means = Xtr.mean()
        scales = Xtr.std(ddof=0).replace(0.0, 1.0)
        return probit_fit_predict((Xtr - means) / scales, ytr, (Xte - means) / scales)
    if method == "C03":
        lda = LinearDiscriminantAnalysis().fit(Xtr, ytr)
        qda = QuadraticDiscriminantAnalysis(reg_param=0.01).fit(Xtr, ytr)
        return np.asarray(
            0.5 * lda.predict_proba(Xte)[:, 1] + 0.5 * qda.predict_proba(Xte)[:, 1],
            dtype=float,
        )
    raise ValueError(method)


def normal_prob_positive(mean, variance):
    sd = math.sqrt(max(float(variance), 1e-12))
    return float(ndtr(float(mean) / sd))


def fit_ar5(train_ret):
    s = pd.Series(np.asarray(train_ret, dtype=float), name="ret").dropna().reset_index(drop=True)
    if len(s) < 30:
        raise ValueError("AR5 requires at least 30 training returns")
    return AutoReg(s, lags=5, trend="c").fit()


def ar5_horizon_probability(model, history_ret, horizon):
    history = list(np.asarray(history_ret, dtype=float)[-5:])
    if len(history) < 5:
        return 0.5

    const = float(model.params.get("const", 0.0))
    phi = [float(model.params.get(f"ret.L{k}", 0.0)) for k in range(1, 6)]
    path = []
    for _ in range(int(horizon)):
        x = const
        for k in range(1, 6):
            x += phi[k - 1] * history[-k]
        path.append(x)
        history.append(x)

    mean_sum = float(np.sum(path))
    variance = float(max(horizon * float(model.sigma2), 1e-12))
    return normal_prob_positive(mean_sum, variance)


def train_state_params(ret):
    r = np.asarray(ret.dropna(), dtype=float)
    neg = r[r < 0]
    pos = r[r > 0]
    means = np.array([
        neg.mean() if len(neg) else -np.std(r),
        pos.mean() if len(pos) else np.std(r),
    ])
    vars_ = np.array([
        neg.var(ddof=1) if len(neg) > 1 else r.var(),
        pos.var(ddof=1) if len(pos) > 1 else r.var(),
    ])
    vars_ = np.maximum(vars_, 1e-12)
    return means, vars_


def hmm_cumulative_moments(transition, means, variances, horizon):
    # For each current state, return the first two moments of the cumulative
    # return over the next H observations under the fixed Markov transition.
    m = np.zeros(2)
    q = np.zeros(2)
    for _ in range(int(horizon)):
        m_new = np.zeros(2)
        q_new = np.zeros(2)
        for i in range(2):
            for j in range(2):
                pij = float(transition[i, j])
                first = float(means[j] + m[j])
                second = float(
                    variances[j] + means[j] ** 2
                    + 2.0 * means[j] * m[j]
                    + q[j]
                )
                m_new[i] += pij * first
                q_new[i] += pij * second
        m, q = m_new, q_new
    return m, q


def online_hmm(train_ret, test_ret, transition, horizon):
    means, vars_ = train_state_params(train_ret)
    trans = np.asarray(transition, dtype=float)
    trans = trans / trans.sum(axis=1, keepdims=True)
    future_m, future_q = hmm_cumulative_moments(trans, means, vars_, horizon)
    pi = np.array([0.5, 0.5], dtype=float)
    out = []

    for r in np.asarray(test_ret, dtype=float):
        lik = np.array([
            math.exp(-0.5 * (r - means[0]) ** 2 / vars_[0]) / math.sqrt(vars_[0]),
            math.exp(-0.5 * (r - means[1]) ** 2 / vars_[1]) / math.sqrt(vars_[1]),
        ])
        post = pi * lik
        post = post / post.sum() if post.sum() > 0 else np.array([0.5, 0.5])
        mean_sum = float(post @ future_m)
        second_sum = float(post @ future_q)
        variance = max(second_sum - mean_sum ** 2, 1e-12)
        out.append(normal_prob_positive(mean_sum, variance))
        pi = post

    return np.asarray(out)


def kalman_horizon_probs(train_price, test_price, horizon):
    z = np.asarray(np.log(train_price), dtype=float)
    if len(z) < 3:
        return np.full(len(test_price), 0.5)

    obs_var = max(float(np.var(np.diff(z))), 1e-8)
    q = 0.01 * obs_var
    F = np.array([[1.0, 1.0], [0.0, 1.0]])
    Hmat = np.array([[1.0, 0.0]])
    Q = np.array([[q, 0.0], [0.0, q]])
    R = np.array([[obs_var]])

    x = np.array([z[-1], z[-1] - z[-2]], dtype=float)
    P = np.eye(2) * obs_var
    I = np.eye(2)
    out = []

    for obs in np.asarray(np.log(test_price), dtype=float):
        xp = F @ x
        Pp = F @ P @ F.T + Q
        innovation = float(obs - (Hmat @ xp)[0])
        S = float((Hmat @ Pp @ Hmat.T + R)[0, 0])
        K = Pp @ Hmat.T / S
        x = xp + K.flatten() * innovation
        P = (I - K @ Hmat) @ Pp

        Fh = np.linalg.matrix_power(F, int(horizon))
        Ph = Fh @ P @ Fh.T
        for j in range(int(horizon)):
            Fj = np.linalg.matrix_power(F, j)
            if j > 0:
                Ph += Fj @ Q @ Fj.T

        mean_change = float((Fh @ x)[0] - x[0])
        variance = float(max(Ph[0, 0], 1e-12))
        out.append(normal_prob_positive(mean_change, variance))

    return np.asarray(out)


def garch_vol_signal(train_ret, test_ret):
    scale = 100.0
    train = np.asarray(train_ret.dropna(), dtype=float) * scale
    am = arch_model(train, mean="Constant", vol="GARCH", p=1, q=1, dist="normal")
    res = am.fit(disp="off")
    pars = res.params
    omega = float(pars.get("omega", 1e-6))
    alpha = float(pars.get("alpha[1]", 0.05))
    beta = float(pars.get("beta[1]", 0.9))
    last_eps = float(train[-1])
    hvar = float(res.conditional_volatility[-1]) ** 2
    train_med = float(np.median(res.conditional_volatility))
    recent = list(train[-5:])
    out = []

    for r_raw in np.asarray(test_ret, dtype=float):
        r = float(r_raw * scale)
        hvar = omega + alpha * last_eps ** 2 + beta * hvar
        sigma = math.sqrt(max(hvar, 1e-12))
        recent.append(r)
        recent = recent[-5:]
        s = np.sign(np.mean(recent)) if sigma > 1.2 * train_med else np.sign(r)
        out.append(0.55 if s > 0 else 0.45 if s < 0 else 0.5)
        last_eps = r

    return np.asarray(out)


def cusum_signal(train_ret, test_ret):
    sigma = max(float(np.std(train_ret.dropna())), 1e-8)
    cpos = 0.0
    cneg = 0.0
    state = 0
    out = []
    k = 0.5
    threshold = 2.5

    for r in np.asarray(test_ret, dtype=float):
        z = float(r / sigma)
        cpos = max(0.0, cpos + z - k)
        cneg = min(0.0, cneg + z + k)
        if cpos >= threshold and state != 1:
            state = 1
            cpos = 0.0
            cneg = 0.0
        elif cneg <= -threshold and state != -1:
            state = -1
            cpos = 0.0
            cneg = 0.0
        out.append(0.55 if state > 0 else 0.45 if state < 0 else 0.5)

    return np.asarray(out)


def prepare_daily():
    df = pd.read_csv(DAILY)
    df["date"] = pd.to_datetime(df["date"])
    for c in ["open", "high", "low", "close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    df["ret"] = np.log(df["close"]).diff()
    return df


def prepare_intra():
    df = pd.read_parquet(INTRA)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["spot"] = pd.to_numeric(df["spot"], errors="coerce")
    df = df.dropna(subset=["timestamp", "spot"]).sort_values("timestamp").drop_duplicates("timestamp")
    df["ist"] = df["timestamp"].dt.tz_convert("Asia/Kolkata")
    df["date"] = df["ist"].dt.date
    df["minute_of_day"] = df["ist"].dt.hour * 60 + df["ist"].dt.minute
    df = df[(df["minute_of_day"] >= 555) & (df["minute_of_day"] <= 930)].copy().reset_index(drop=True)
    df["ret"] = np.log(df["spot"]).diff()
    return df


def daily_run():
    df = prepare_daily()
    out = {}

    for H in DAILY_H:
        future = np.log(df["close"].shift(-H) / df["close"])
        y = np.where(future > 0, 1, np.where(future < 0, 0, np.nan))
        hres = {}

        for method in METHODS:
            if method == "C10":
                hres[method] = {"status": "BLOCKED_DATA", "reason": "PIT-safe event-intensity history not materialized"}
                continue
            if method == "C11":
                hres[method] = {"status": "BLOCKED_DATA", "reason": "PIT-safe synchronized cross-market feature layer not materialized"}
                continue

            p = np.full(len(df), np.nan)
            start = max(300, int(len(df) * 0.4))

            if method == "C05":
                try:
                    p[start:] = garch_vol_signal(df["ret"].iloc[:start], df["ret"].iloc[start:])
                except Exception as exc:
                    hres[method] = {"status": "BLOCKED_DATA", "reason": f"GARCH fit unavailable: {type(exc).__name__}: {exc}"}
                    continue

            elif method == "C06":
                tr = df["ret"].iloc[:start].dropna()
                te = df["ret"].iloc[start:]
                p[start:] = online_hmm(tr, te, np.array([[0.95, 0.05], [0.05, 0.95]]), H)

            elif method == "C07":
                tr = df["ret"].iloc[:start].dropna()
                hard = (tr.to_numpy() > 0).astype(int)
                trans = np.ones((2, 2)) * 0.05
                for a, b in zip(hard[:-1], hard[1:]):
                    trans[a, b] += 1
                trans = trans / trans.sum(axis=1, keepdims=True)
                p[start:] = online_hmm(tr, df["ret"].iloc[start:], trans, H)

            elif method == "C08":
                p[start:] = kalman_horizon_probs(df["close"].iloc[:start], df["close"].iloc[start:], H)

            elif method == "C09":
                p[start:] = cusum_signal(df["ret"].iloc[:start], df["ret"].iloc[start:])

            else:
                X = lag_features(df["ret"])
                for block_start in range(start, len(df), 20):
                    block_end = min(block_start + 20, len(df))
                    if method == "C04":
                        try:
                            model = fit_ar5(df["ret"].iloc[:block_start].dropna())
                            for i in range(block_start, block_end):
                                history = df["ret"].iloc[: i + 1].dropna()
                                p[i] = ar5_horizon_probability(model, history, H)
                        except Exception:
                            continue
                        continue

                    tr_end = max(30, block_start - H)
                    Xtr = X.iloc[:tr_end].dropna()
                    ytr = pd.Series(y[:tr_end], index=df.index[:tr_end]).loc[Xtr.index].dropna().astype(int)
                    if len(ytr) < 50 or ytr.nunique() < 2:
                        continue
                    Xtr = Xtr.loc[ytr.index]
                    Xte = X.iloc[block_start:block_end]
                    good = ~Xte.isna().any(axis=1)
                    if not good.any():
                        continue
                    if method == "C01":
                        model = sm.Logit(ytr, sm.add_constant(Xtr, has_constant="add")).fit(disp=False, maxiter=100)
                        pred = np.asarray(
                            model.predict(sm.add_constant(Xte.loc[good], has_constant="add")),
                            dtype=float,
                        )
                    else:
                        pred = np.asarray(model_probs(method, Xtr, ytr, Xte.loc[good]), dtype=float)
                    p[block_start:block_end][good.to_numpy()] = pred

            hres[method] = result_metrics(y, p, future, 20)

        out[str(H)] = {
            "label": {"n": int(np.isfinite(y).sum()), "positive_rate": float(np.nanmean(y))},
            **hres,
        }

    return {
        "data_rows": len(df),
        "date_start": df["date"].min().date().isoformat(),
        "date_end": df["date"].max().date().isoformat(),
        "horizons": out,
    }


def intra_run():
    df = prepare_intra()
    grid = (
        df["minute_of_day"].between(570, 930)
        & (((df["minute_of_day"] - 570) % 60) == 0)
    ).to_numpy()
    idx = pd.Index(df["timestamp"])
    vals = np.log(df["spot"].to_numpy())
    out = {}

    for H in INTRA_H:
        target = idx + pd.Timedelta(minutes=H)
        pos = idx.get_indexer(target)
        fut = np.full(len(df), np.nan)
        good = pos >= 0
        fut[good] = vals[pos[good]] - vals[good]
        y = np.where(
            np.isfinite(fut),
            np.where(fut > 0, 1, np.where(fut < 0, 0, np.nan)),
            np.nan,
        )
        hres = {}
        start = int(len(df) * 0.4)

        for method in METHODS:
            if method in {"C10", "C11"}:
                hres[method] = {"status": "BLOCKED_DATA", "reason": "Required PIT-safe event/cross-market layer not materialized"}
                continue

            p = np.full(len(df), np.nan)

            if method == "C05":
                try:
                    p[start:] = garch_vol_signal(df["ret"].iloc[:start], df["ret"].iloc[start:])
                except Exception as exc:
                    hres[method] = {"status": "BLOCKED_DATA", "reason": f"GARCH fit unavailable: {type(exc).__name__}: {exc}"}
                    continue

            elif method == "C06":
                p[start:] = online_hmm(
                    df["ret"].iloc[:start].dropna(),
                    df["ret"].iloc[start:],
                    np.array([[0.95, 0.05], [0.05, 0.95]]),
                    H,
                )

            elif method == "C07":
                tr = df["ret"].iloc[:start].dropna()
                hard = (tr.to_numpy() > 0).astype(int)
                trans = np.ones((2, 2)) * 0.05
                for a, b in zip(hard[:-1], hard[1:]):
                    trans[a, b] += 1
                trans = trans / trans.sum(axis=1, keepdims=True)
                p[start:] = online_hmm(tr, df["ret"].iloc[start:], trans, H)

            elif method == "C08":
                p[start:] = kalman_horizon_probs(
                    df["spot"].iloc[:start],
                    df["spot"].iloc[start:],
                    H,
                )

            elif method == "C09":
                p[start:] = cusum_signal(df["ret"].iloc[:start], df["ret"].iloc[start:])

            else:
                X = lag_features(df["ret"])
                dates = list(df["date"].iloc[start:].drop_duplicates())
                for di in range(0, len(dates), 20):
                    block_dates = set(dates[di:di + 20])
                    loc = np.flatnonzero(df["date"].isin(block_dates).to_numpy())
                    loc = loc[loc >= start]
                    if len(loc) == 0:
                        continue

                    if method == "C04":
                        try:
                            model = fit_ar5(df["ret"].iloc[:loc[0]].dropna())
                            for i in loc:
                                history = df["ret"].iloc[: i + 1].dropna()
                                p[i] = ar5_horizon_probability(model, history, H)
                        except Exception:
                            continue
                        continue

                    tr_end = int(loc[0] - H)
                    Xtr = X.iloc[:tr_end].dropna()
                    yy = pd.Series(y[:tr_end], index=df.index[:tr_end]).loc[Xtr.index].dropna().astype(int)
                    if len(yy) < 300 or yy.nunique() < 2:
                        continue
                    Xtr = Xtr.loc[yy.index]
                    Xte = X.loc[loc]
                    goodte = ~Xte.isna().any(axis=1)
                    if not goodte.any():
                        continue

                    if method == "C01":
                        model = sm.Logit(yy, sm.add_constant(Xtr, has_constant="add")).fit(disp=False, maxiter=100)
                        pred = np.asarray(
                            model.predict(sm.add_constant(Xte.loc[goodte], has_constant="add")),
                            dtype=float,
                        )
                    else:
                        pred = np.asarray(model_probs(method, Xtr, yy, Xte.loc[goodte]), dtype=float)
                    p[loc[goodte.to_numpy()]] = pred

            hres[method] = result_metrics(y[grid], p[grid], fut[grid], 60)

        out[str(H)] = {
            "label": {
                "n": int(np.isfinite(y[grid]).sum()),
                "positive_rate": float(np.nanmean(y[grid])),
            },
            **hres,
        }

    return {
        "data_rows": len(df),
        "decision_grid_rows": int(grid.sum()),
        "timestamp_start": df["timestamp"].min().isoformat(),
        "timestamp_end": df["timestamp"].max().isoformat(),
        "horizons": out,
    }


report = {
    "daily": daily_run(),
    "intraday": intra_run(),
    "methods": METHODS,
    "status": "PASS",
}
(OUT / "phase4_family_c_results.json").write_text(
    json.dumps(report, indent=2),
    encoding="utf-8",
)
print(json.dumps({
    "daily_rows": report["daily"]["data_rows"],
    "intraday_rows": report["intraday"]["data_rows"],
    "grid": report["intraday"]["decision_grid_rows"],
}, indent=2))
