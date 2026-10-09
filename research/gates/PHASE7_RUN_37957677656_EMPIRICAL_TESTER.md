# Independent Tester Report — Phase 7 Run #37957677656

**Decision: PASS WITH SCOPED RESTRICTIONS — artifact integrity, source alignment, metric reconciliation and family inference**

- Source run: https://github.com/vishnuvcr/Naked-option-v1/actions/runs/37957677656
- Exact developer commit: b50be8cfa1ebe008a800e65a53f9c0fb2581aecb
- Pinned tester audit-code commit: 50334eb728a85ae8ca88f9ded5246b867c9cb56f
- Independent checks passed: 3098
- Independent checks failed: 0
- Exact run/commit identity verified: True
- Scientific promotion: **NOT GRANTED by this technical audit alone**
- Phase 8 remains gated until this report is reviewed and any other required data/source gates pass.

## Audit summary

{
  "family_tests_checked": 10,
  "layers": {
    "daily": {
      "horizons": {
        "1": {
          "P08": {
            "accuracy": 0.5303867403314917,
            "balanced_accuracy": 0.4964616785697167,
            "brier": 0.24910202758722985,
            "n": 1448,
            "roc_auc": 0.5213440061352633
          },
          "family_max_brier_improvement": 0.0002831739612465891,
          "family_p_value": 0.784,
          "n_rows": 1670
        },
        "10": {
          "P08": {
            "accuracy": 0.5576388888888889,
            "balanced_accuracy": 0.4944037670282704,
            "brier": 0.24497112633810186,
            "n": 1440,
            "roc_auc": 0.5460695514945917
          },
          "family_max_brier_improvement": 0.002968753042771257,
          "family_p_value": 0.506,
          "n_rows": 1670
        },
        "2": {
          "P08": {
            "accuracy": 0.544574982722875,
            "balanced_accuracy": 0.4950632178361162,
            "brier": 0.24808080123330017,
            "n": 1447,
            "roc_auc": 0.524545893253547
          },
          "family_max_brier_improvement": 0.00047893026517605605,
          "family_p_value": 0.69,
          "n_rows": 1670
        },
        "3": {
          "P08": {
            "accuracy": 0.544574982722875,
            "balanced_accuracy": 0.49511478282348764,
            "brier": 0.24900342696885186,
            "n": 1447,
            "roc_auc": 0.5060324664798648
          },
          "family_max_brier_improvement": -0.00034422893991136236,
          "family_p_value": 0.938,
          "n_rows": 1670
        },
        "5": {
          "P08": {
            "accuracy": 0.556401384083045,
            "balanced_accuracy": 0.4997824676711999,
            "brier": 0.24793892543103074,
            "n": 1445,
            "roc_auc": 0.5080117933598257
          },
          "family_max_brier_improvement": 0.0005684826685222812,
          "family_p_value": 0.764,
          "n_rows": 1670
        }
      },
      "panels": 5
    },
    "intraday": {
      "horizons": {
        "120": {
          "P08": {
            "accuracy": 0.5101898623933113,
            "balanced_accuracy": 0.4954874821624125,
            "brier": 0.2500957329162175,
            "n": 5741,
            "roc_auc": 0.5114639225756978
          },
          "family_max_brier_improvement": 0.000272561287398045,
          "family_p_value": 0.544,
          "n_rows": 8441
        },
        "15": {
          "P08": {
            "accuracy": 0.5019220208676551,
            "balanced_accuracy": 0.4946919555880457,
            "brier": 0.2509219522581964,
            "n": 7284,
            "roc_auc": 0.48267987631117326
          },
          "family_max_brier_improvement": -0.0002474263556118872,
          "family_p_value": 0.994,
          "n_rows": 8441
        },
        "30": {
          "P08": {
            "accuracy": 0.5194288068103803,
            "balanced_accuracy": 0.4994643520268508,
            "brier": 0.25013809677164456,
            "n": 7283,
            "roc_auc": 0.4951680639894994
          },
          "family_max_brier_improvement": -0.0003254484404661451,
          "family_p_value": 1.0,
          "n_rows": 8441
        },
        "5": {
          "P08": {
            "accuracy": 0.5007558059639962,
            "balanced_accuracy": 0.4961644524444231,
            "brier": 0.25080273809711645,
            "n": 7277,
            "roc_auc": 0.4782025008948604
          },
          "family_max_brier_improvement": 0.0006639740305077532,
          "family_p_value": 0.262,
          "n_rows": 8441
        },
        "60": {
          "P08": {
            "accuracy": 0.5089106064961195,
            "balanced_accuracy": 0.4972232283488328,
            "brier": 0.25026578231650526,
            "n": 6958,
            "roc_auc": 0.5073538645996007
          },
          "family_max_brier_improvement": -0.000218264116890492,
          "family_p_value": 0.994,
          "n_rows": 8441
        }
      },
      "panels": 5
    }
  },
  "per_cell_metrics_checked": 100
}

## Tester to Developer

Resolve failed integrity/source/numerical checks, preserve this report, and resubmit through the same independent gate. Do not change the frozen scientific method to make a failure disappear.

## Developer to Tester

Audit all ten panels, row alignment, P10 abstention, regime eligibility, P05/P06 masks, family bootstrap, hashes, aggregate metrics and inference independently. Do not advance Phase 8 based on a code-gate pass or a failed empirical audit.
