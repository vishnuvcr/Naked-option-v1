"""Pre-registered prediction metrics and inference utilities.

These functions operate on caller-supplied arrays only. They never open market data and do
not authorize model fitting. Bootstrap input must be paired, per-exchange-session loss
improvement (baseline log loss minus candidate log loss), grouped by outer validation fold.
"""
from __future__ import annotations

import math
import random
import statistics
from numbers import Integral, Real
from collections.abc import Mapping, Sequence
from typing import Any

EPSILON = 1e-6


def _validate_binary_inputs(y_true: Sequence[int], probabilities: Sequence[float]) -> tuple[list[int], list[float]]:
    if len(y_true) != len(probabilities) or not y_true:
        raise ValueError("y_true and probabilities must have equal, nonzero lengths")
    y: list[int] = []
    p: list[float] = []
    for value in y_true:
        if isinstance(value, bool) or not isinstance(value, Integral) or value not in (0, 1):
            raise ValueError("binary labels must be integer 0 or 1 (bool and float labels are not accepted)")
        y.append(int(value))
    for value in probabilities:
        if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(float(value)):
            raise ValueError("probabilities must be finite numeric values")
        if not 0.0 <= float(value) <= 1.0:
            raise ValueError("probabilities must be in [0, 1]")
        p.append(min(1.0 - EPSILON, max(EPSILON, float(value))))
    return y, p


def binary_log_loss(y_true: Sequence[int], probabilities: Sequence[float]) -> float:
    """Mean binary log loss with the preregistered epsilon clipping."""
    y, p = _validate_binary_inputs(y_true, probabilities)
    return statistics.fmean(-(yi * math.log(pi) + (1 - yi) * math.log(1 - pi)) for yi, pi in zip(y, p))


def brier_score(y_true: Sequence[int], probabilities: Sequence[float]) -> float:
    """Mean squared probability error."""
    y, p = _validate_binary_inputs(y_true, probabilities)
    return statistics.fmean((pi - yi) ** 2 for yi, pi in zip(y, p))


def balanced_accuracy(y_true: Sequence[int], probabilities: Sequence[float], threshold: float = 0.5) -> float:
    """Mean of sensitivity and specificity; both classes must be present."""
    y, p = _validate_binary_inputs(y_true, probabilities)
    if not math.isfinite(threshold) or not 0.0 < threshold < 1.0:
        raise ValueError("threshold must be finite and strictly between 0 and 1")
    positive = [pi >= threshold for pi in p]
    pos_n = sum(yi == 1 for yi in y)
    neg_n = sum(yi == 0 for yi in y)
    if pos_n == 0 or neg_n == 0:
        raise ValueError("balanced accuracy requires both binary classes")
    sensitivity = sum(yi == 1 and pred for yi, pred in zip(y, positive)) / pos_n
    specificity = sum(yi == 0 and not pred for yi, pred in zip(y, positive)) / neg_n
    return 0.5 * (sensitivity + specificity)


def _sigmoid(value: float) -> float:
    if value >= 0:
        expv = math.exp(-min(value, 700.0))
        return 1.0 / (1.0 + expv)
    expv = math.exp(max(value, -700.0))
    return expv / (1.0 + expv)


def _logit(probability: float) -> float:
    p = min(1.0 - EPSILON, max(EPSILON, probability))
    return math.log(p / (1.0 - p))


def calibration_intercept_slope(
    y_true: Sequence[int],
    probabilities: Sequence[float],
    *,
    max_iterations: int = 100,
    tolerance: float = 1e-9,
) -> dict[str, float | int | str]:
    """Fit logistic calibration y ~ intercept + slope*logit(p) by Newton steps.

    This reports the calibration fit and convergence state; it must be run on scored
    evaluation predictions only for measurement, never used to recalibrate those predictions.
    """
    y, p = _validate_binary_inputs(y_true, probabilities)
    if set(y) != {0, 1}:
        raise ValueError("calibration intercept/slope requires both binary classes")
    if isinstance(max_iterations, bool) or not isinstance(max_iterations, Integral) or max_iterations < 1 or tolerance <= 0:
        raise ValueError("max_iterations must be a positive integer and tolerance must be positive")
    x = [_logit(pi) for pi in p]
    intercept, slope = 0.0, 1.0
    ridge = 1e-10
    converged = False
    for iteration in range(1, max_iterations + 1):
        q = [_sigmoid(intercept + slope * xi) for xi in x]
        w = [qi * (1.0 - qi) for qi in q]
        g0 = sum(qi - yi for qi, yi in zip(q, y))
        g1 = sum((qi - yi) * xi for qi, yi, xi in zip(q, y, x))
        h00 = sum(w)
        h01 = sum(wi * xi for wi, xi in zip(w, x))
        h11 = sum(wi * xi * xi for wi, xi in zip(w, x))
        h00 += ridge
        h11 += ridge
        determinant = h00 * h11 - h01 * h01
        if determinant <= 1e-18 or not math.isfinite(determinant):
            return {"intercept": intercept, "slope": slope, "iterations": iteration, "status": "NON_IDENTIFIABLE"}
        step0 = (h11 * g0 - h01 * g1) / determinant
        step1 = (h00 * g1 - h01 * g0) / determinant
        scale = 1.0
        old_norm = abs(g0) + abs(g1)
        # Dampen overly large steps for numerical stability.
        while scale > 1.0 / 1024.0:
            new_a = intercept - scale * step0
            new_b = slope - scale * step1
            new_q = [_sigmoid(new_a + new_b * xi) for xi in x]
            new_g0 = sum(qi - yi for qi, yi in zip(new_q, y))
            new_g1 = sum((qi - yi) * xi for qi, yi, xi in zip(new_q, y, x))
            if abs(new_g0) + abs(new_g1) <= old_norm or not math.isfinite(old_norm):
                break
            scale *= 0.5
        intercept, slope = new_a, new_b
        if max(abs(scale * step0), abs(scale * step1)) < tolerance:
            converged = True
            break
    return {
        "intercept": float(intercept),
        "slope": float(slope),
        "iterations": iteration,
        "status": "CONVERGED" if converged else "NOT_CONVERGED",
    }


def _percentile(sorted_values: Sequence[float], probability: float) -> float:
    if not sorted_values:
        raise ValueError("cannot calculate a percentile for an empty sequence")
    if not 0.0 <= probability <= 1.0:
        raise ValueError("percentile probability must lie in [0, 1]")
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(sorted_values[lower])
    weight = position - lower
    return float(sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight)


def paired_moving_block_bootstrap(
    fold_session_deltas: Sequence[Sequence[float]],
    *,
    block_length: int = 5,
    replicates: int = 10_000,
    seed: int = 2026101209,
    confidence_level: float = 0.95,
) -> dict[str, Any]:
    """Bootstrap paired session-level improvement without crossing outer-fold boundaries.

    Positive delta means baseline log loss minus candidate log loss, so positive favors
    the candidate. Each fold is resampled separately in contiguous moving blocks; the
    same precomputed per-session paired difference preserves candidate/baseline pairing.
    """
    if not fold_session_deltas or any(not fold for fold in fold_session_deltas):
        raise ValueError("at least one non-empty outer-fold session-delta sequence is required")
    if isinstance(block_length, bool) or not isinstance(block_length, Integral) or block_length < 1:
        raise ValueError("block_length must be a positive integer")
    if isinstance(replicates, bool) or not isinstance(replicates, Integral) or replicates < 1:
        raise ValueError("replicates must be a positive integer")
    if isinstance(seed, bool) or not isinstance(seed, Integral):
        raise ValueError("seed must be an integer")
    block_length = int(block_length)
    replicates = int(replicates)
    seed = int(seed)
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be in (0, 1)")
    folds: list[list[float]] = []
    for fold_index, values in enumerate(fold_session_deltas):
        row = [float(value) for value in values]
        if len(row) < block_length:
            raise ValueError(f"fold {fold_index} has {len(row)} sessions, less than block_length={block_length}")
        if any(not math.isfinite(value) for value in row):
            raise ValueError(f"fold {fold_index} contains non-finite improvement")
        folds.append(row)

    flattened = [value for fold in folds for value in fold]
    observed = statistics.fmean(flattened)
    rng = random.Random(seed)
    estimates: list[float] = []
    for _ in range(replicates):
        sampled_all: list[float] = []
        for fold in folds:
            n = len(fold)
            sampled: list[float] = []
            while len(sampled) < n:
                start = rng.randrange(0, n - block_length + 1)
                sampled.extend(fold[start : start + block_length])
            sampled_all.extend(sampled[:n])
        estimates.append(statistics.fmean(sampled_all))

    estimates.sort()
    unique_estimates = len(set(estimates))
    if unique_estimates == 1:
        # A degenerate empirical resampling distribution cannot support a confidence
        # interval or a significance test. Preserve the observed mean descriptively,
        # but fail closed rather than returning a zero-width interval and minimum p-value.
        return {
            "observed_mean_improvement": observed,
            "confidence_level": confidence_level,
            "ci_low": None,
            "ci_high": None,
            "raw_two_sided_p_value_centered_bootstrap": None,
            "block_length_exchange_sessions": block_length,
            "replicates": replicates,
            "seed": seed,
            "fold_session_counts": [len(fold) for fold in folds],
            "positive_favors_candidate": True,
            "inferential_status": "NON_IDENTIFIABLE_DEGENERATE_RESAMPLING",
            "bootstrap_unique_estimates": unique_estimates,
        }

    alpha = (1.0 - confidence_level) / 2.0
    ci_low = _percentile(estimates, alpha)
    ci_high = _percentile(estimates, 1.0 - alpha)
    exceedances = sum(abs(value - observed) >= abs(observed) for value in estimates)
    raw_p = (1 + exceedances) / (replicates + 1)
    return {
        "observed_mean_improvement": observed,
        "confidence_level": confidence_level,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "raw_two_sided_p_value_centered_bootstrap": raw_p,
        "block_length_exchange_sessions": block_length,
        "replicates": replicates,
        "seed": seed,
        "fold_session_counts": [len(fold) for fold in folds],
        "positive_favors_candidate": True,
        "inferential_status": "OK",
        "bootstrap_unique_estimates": unique_estimates,
    }


def benjamini_yekutieli(
    p_values: Mapping[str, float],
    *,
    q: float = 0.05,
) -> dict[str, dict[str, float | bool]]:
    """BY FDR control and adjusted p-values for one frozen hypothesis family."""
    if not 0.0 < q < 1.0:
        raise ValueError("q must be in (0, 1)")
    if not p_values:
        return {}
    items = list(p_values.items())
    for name, p in items:
        if not isinstance(name, str) or not name:
            raise ValueError("hypothesis IDs must be non-empty strings")
        if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(float(p)) or not 0.0 <= float(p) <= 1.0:
            raise ValueError(f"invalid p-value for {name!r}: {p!r}")
    items.sort(key=lambda item: (float(item[1]), item[0]))
    m = len(items)
    harmonic = math.fsum(1.0 / rank for rank in range(1, m + 1))
    factor = m * harmonic
    adjusted_sorted: list[float] = [1.0] * m
    running_min = 1.0
    for index in range(m - 1, -1, -1):
        rank = index + 1
        candidate = float(items[index][1]) * factor / rank
        running_min = min(running_min, candidate)
        adjusted_sorted[index] = min(1.0, running_min)
    reject_cutoff_rank = 0
    for index, (_, p) in enumerate(items, start=1):
        if float(p) <= index * q / factor:
            reject_cutoff_rank = index
    rejected_ids = {name for name, _ in items[:reject_cutoff_rank]}
    return {
        name: {
            "raw_p_value": float(p),
            "by_adjusted_p_value": adjusted_sorted[index],
            "reject_at_q": name in rejected_ids,
        }
        for index, (name, p) in enumerate(items)
    }
