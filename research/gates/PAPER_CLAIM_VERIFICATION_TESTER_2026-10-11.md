# Tester Report — Rendered Uploaded-Paper Claim Checks

- Review date: 2026-10-11 UTC.
- Reviewed developer commit: `c4ecb0047a2acdd0bc008106bd1e4c1fd347f3a4`.
- Claim-audit note blob SHA: `766134e809d141a6142d931074b9ee52f0ca2e8b`.
- Source coverage audit blob SHA: `f1cd07f41a1314ea0580ac1a32fa3f3106168edf`.
- Role limitation: the source pages and arithmetic were checked in the tester role in the same connected assistant session. This is not a separate human reviewer or independent AI reviewer; it must not be presented as such.

## Scope and verdict

**PASS WITH SCOPED RESTRICTIONS — source-note arithmetic / consistency review only.** The sampled rendered source pages support the specific findings below. This is not certification of every claim in all 15 PDFs and does not authorize data acquisition, model fitting/scoring, holdout access, or options P&L testing.

## Rechecks

1. **IJCSE PCR rule coverage — confirmed.** Stated classes are bearish for PCR < 0.8, neutral for 0.8–0.9 inclusive, and bullish for PCR > 1. The gap (0.9 < PCR \le 1) is unassigned, yet the source's example table labels PCR=0.91 Neutral. That example is not implied by the written piecewise function.
2. **JRFM parameter arithmetic — confirmed.** Displayed model summary: (17{,}920 + 12{,}416 + 0 + 33 = 30{,}369). The summary prints 30,369; surrounding prose prints 330,369. The source note correctly marks the intended prose count as unresolved rather than guessing.
3. **Bansal et al. R² interpretation — confirmed.** Table II reports LSTM average R² = −0.11, while the next-page prose calls −0.11 “close” to +1. The wording is mathematically inconsistent. The data do show LSTM as the least-negative average among the listed models, which is distinct from establishing strong predictive skill.
4. **Cureus SVR metrics — confirmed in the rendered table.** Visible rows include 5-year SVR test R² −47.8984 / RMSE 6,079.98 / MAE 6,019.04 and 10-year SVR test R² −154.8147 / RMSE 12,296.97 / MAE 12,255.35. These must be preserved as negative author-reported results, not converted into a generic model accuracy score.

## Data/method boundaries

- Source page checks are literature-audit evidence only; no project model was fitted or scored.
- Frozen PPR-3 configuration files and their manifest have not been changed.
- No live-source request, market-data download, encryption/decryption, holdout read or strategy/P&L operation was performed.
- The split-recovery gate remains independently denied. This report does not mutate its authorization flags.

**Tester → Developer:** Correct the source note only if a page locator/value is wrong; keep these findings linked to source PDFs and do not promote author metrics as project evidence.

**Developer → Tester:** Any update affecting frozen protocol files needs a new exact-SHA review. Continue to keep empirical permissions separate from literature review decisions.
