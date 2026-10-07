# Phase 6 Novel Methods — Frozen Method Specification

Date: 2026-10-07
Status: developer resubmission after tester request-changes
Scope: Family E (E01-E10) and Family I (I01-I10)

## Global conventions

- Raw return for horizon k is log price change over exactly k observations/sessions on the canonical point-in-time path.
- All rolling windows are causal and right-aligned.
- When a learned normalization or empirical probability is needed, it is fit only on the chronological training block for the current walk-forward fit.
- Fixed cutpoints below are never tuned from test results.
- If a required input is absent or fails PIT validation, the method/horizon is BLOCKED_DATA.
- For intraday, feature construction may use the full 1-minute path but evaluation occurs only at the frozen hourly decision rows.
- Signed scores are oriented so positive means bullish NIFTY pressure.

## Family E

### E01 Hurst with random-walk/surrogate controls
Window: 256 return observations.
Estimator: rescaled-range Hurst estimate from cumulative demeaned returns using the fixed subwindow sizes {16,32,64,128,256}; regress log(R/S) on log(n) with ordinary least squares.
Control: within each training fit, create one fixed-seed shuffled-return surrogate of the same window and report H_real - H_shuffle.
Signal: bullish if H_real > 0.5 and recent 20-observation return is positive; bearish if H_real > 0.5 and recent return is negative; otherwise p=0.5.
Seed: 42.

### E02 Multifractal / MFDFA diagnostic
Window: 256 returns.
Scales: {8,16,32,64}.
q grid: {-3,-2,-1,0,1,2,3}.
For each q and scale, use the standard detrended fluctuation RMS of linear-detrended segments; estimate h(q) from OLS slope of log(F_q) on log(scale).
Signal score: delta_h = h(-3)-h(3); signed direction uses sign of the latest 20-observation return when delta_h > 0.10, otherwise neutral.
No centered windows.

### E03 Sample entropy
Window: 100 returns.
Embedding dimension m=2.
Tolerance r=0.20 * training-window standard deviation.
Use standard sample-entropy logarithmic ratio with self-matches excluded.
Signal: entropy below the training-block median implies trend-persistent state; use recent return sign with p=0.55/0.45. Otherwise p=0.50.
The training median is computed only inside the current fit.

### E04 Permutation entropy
Window: 100 returns; ordinal pattern order m=5; delay=1.
Compute normalized permutation entropy from the six? No: all 5! = 120 ordinal patterns.
Signal: normalized entropy < 0.80 => persistent state and use recent return sign with p=0.55/0.45; otherwise p=0.50.
The 0.80 threshold is fixed.

### E05 Complexity / roughness
Window: 60 returns.
Define roughness R = mean(|r_t-r_{t-1}|) / (mean(|r_t|)+1e-12).
Normalize by dividing R by its training-block median.
Signal: R_norm > 1.25 => mean-reverting/contrarian (flip recent return sign); R_norm < 0.75 => persistence (keep sign); otherwise p=0.50.

### E06 Mutual information
Candidate source lags: 1,2,5,10 observations.
Discretize each source return into 8 equal-frequency bins using training-block quantiles.
Compute plug-in mutual information I(X_lag;Y_H) with Laplace +1 cell smoothing using only eligible training observations.
Select the source lag with largest training MI; ties go to the smallest lag.
At test time, estimate P(Y_H=1 | selected-lag-bin) from the same training table and use that probability.
No test labels enter lag selection or probability estimation.

### E07 Transfer entropy / information flow
Source: predeclared global risk-on/off composite from the accepted daily global layer when available, using only the most recently completed source session at the NIFTY decision timestamp.
Discretization: source and NIFTY returns into 3 equiprobable bins using training quantiles.
History: one lag for source and one lag for target.
Estimate first-order transfer entropy TE(source -> NIFTY) from conditional-frequency counts with +1 Laplace smoothing.
Use a fixed TE threshold equal to 0.02 nats: if TE <= threshold, p=0.50; otherwise use the training conditional direction table for the current source state.
If the composite lacks PIT-safe observations, BLOCKED_DATA.

### E08 Regime-conditioned model switching
Regime axes are fixed:
- volatility state = low/mid/high from the causal 252-observation percentile rank of 20-observation volatility with cutpoints 0.33 and 0.67;
- trend state = negative/neutral/positive from the sign of the 20-observation EMA slope, neutral if absolute slope is below 0.25 * training-window volatility.
Fixed model map:
- low volatility -> D09 spline regardless of trend state;
- mid volatility -> D02 ExtraTrees;
- high volatility -> D12 shallow MLP.
The map is fixed before seeing Phase 6 results and never changed by observed performance.

### E09 Volatility-state classifier
Use the same fixed low/mid/high volatility states as E08.
For each state, estimate the training-only probability of Y_H=1.
At test time, output the state-specific empirical probability.
If a state has <50 eligible training observations, back off to the pooled training probability; this threshold is fixed.

### E10 Trend/volatility regime matrix
Use the E08 trend state and volatility state.
Form the fixed 3x3 state matrix and estimate P(Y_H=1 | state cell) from eligible training labels.
Cells with <50 observations back off first to the trend-marginal probability, then to the volatility-marginal probability, then to the pooled training probability.
All backoff rules are deterministic and fixed.

## Family I

### I01 Multi-scale directional pressure
Scales k={3,10,30} observations.
For each scale, z_k = return_k / (rolling 60-observation standard deviation * sqrt(k)+1e-12).
Score = (z_3 + z_10/sqrt(10/3) + z_30/sqrt(30/3)) / 3.
Probability = sigmoid(1.5 * score).
Positive score is bullish.

### I02 Cross-market lead-lag pressure
Fixed sources: SENSEX, Bank Nifty, S&P 500, Nasdaq Composite, Nikkei 225, Hang Seng.
Use the most recently completed source observation available at the NIFTY decision timestamp.
Each source return is standardized by its own causal 60-observation rolling standard deviation.
Equal-weight the available standardized returns.
If fewer than 4 of the 6 sources are PIT-available for a decision, the method is BLOCKED_DATA for that run; no dynamic source selection is permitted.
Map score to probability with sigmoid(score).

### I03 Volatility-adjusted trend persistence
Window: 30 observations.
Compute persistence = sum(sign(r_j)*|r_j|) / (sum(|r_j|)+1e-12).
Compute vol-adjusted score = persistence / (rolling 60-observation volatility + 1e-12), clipped to [-3,3].
Probability = sigmoid(score).

### I04 Option-surface directional asymmetry
Required PIT-safe inputs: 25-delta put IV, 25-delta call IV, ATM IV, put OI, call OI at the nearest valid weekly expiry.
Use:
- skew = IV_put25 - IV_call25;
- oi_pressure = log((call_OI+1)/(put_OI+1));
- iv_rv = ATM_IV / (rolling 20-observation realized volatility + 1e-12).
Causal 60-observation z-scores for each component.
Signed score = -z(skew) + 0.5*z(oi_pressure) - 0.5*z(iv_rv).
Probability = sigmoid(score).
If any required surface input is not demonstrably PIT-available, BLOCKED_DATA.

### I05 Regime-transition pressure
Use the 9-state E10 regime matrix.
Within training data, estimate a 9x9 transition matrix between consecutive regime states.
Also estimate P(Y_H=1 | destination regime) from training data.
At test time, the current regime's transition probabilities are multiplied by destination-regime directional probabilities and summed to obtain p_up.
This is a fixed one-step transition forecast; no test-period re-estimation is allowed.

### I06 Liquidity-friction-adjusted signal quality
Required PIT-safe liquidity inputs: quoted spread proxy or bid/ask spread and traded volume/OI.
Base signal = I01 signed score.
Friction ratio = current spread / causal 60-observation median spread.
Liquidity factor = 1 / (1 + max(friction ratio,0)).
Adjusted score = base score * liquidity factor.
Probability = sigmoid(1.5 * adjusted score).
If spread/liquidity inputs are unavailable, BLOCKED_DATA.

### I07 Probability-of-move-vs-premium efficiency
Required PIT-safe ATM CE/PE premium, strike, spot and expiry.
For each side, compute the fixed option break-even underlying return from the observed premium and strike, then estimate the training-only probability that the H-horizon underlying return exceeds the relevant break-even threshold.
Efficiency score = P(move beyond break-even) / (premium/spot + 1e-12).
Report the larger CE/PE score and its side.
No option contract may be selected using future information. If PIT-safe premiums are unavailable, BLOCKED_DATA.

### I08 Entropy-weighted ensemble confidence
Fixed component probabilities: D01, D02, D03, D07, D09, D12.
For each component, compute Shannon entropy H(p) = -p*log2(p)-(1-p)*log2(1-p).
Weight w = 1-H(p), floored at 0.05.
Ensemble probability = sum(w*p)/sum(w).
Confidence score = 2*|p_ensemble-0.5|.
No component selection or weight tuning is permitted.

### I09 Abstention / edge-density score
Base probability: D07.
Fixed abstention band: [0.45,0.55].
Trade only outside the band.
Coverage = fraction of evaluable observations outside the band.
Edge-density score = mean(|p-0.5|) conditional on non-abstention.
Report both coverage and conditional directional metrics; abstained observations are not silently omitted from denominator reporting.

### I10 Direction Conviction State
Required components: I01, I02, I03, E09, I08.
Convert each to a signed score in [-1,1]:
- s1=2*I01_p-1
- s2=2*I02_p-1
- s3=tanh(I03_score)
- s4=2*E09_p-1
- s5=2*I08_p-1
Composite S = 0.20*(s1+s2+s3+s4+s5).
Probability = sigmoid(2*S).
Bullish state if S >= 0.20; bearish if S <= -0.20; otherwise neutral.
If any required component is BLOCKED_DATA, I10 is BLOCKED_DATA rather than reweighted.

## Universal Phase 6 regression requirements

1. Future-row mutation invariance for every causal rolling/entropy/information feature.
2. No centered/symmetric window in any registered feature.
3. Training-only quantile/binning/scaling assertions.
4. Regime-state and backoff determinism.
5. D08/E08/I08 component model provenance and no result-driven model selection.
6. Exact fixed thresholds and weights tested against configuration constants.
7. Probability outputs finite and in [0,1].
8. All methods persist explicit data-status reasons when blocked.
