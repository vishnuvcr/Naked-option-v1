from pathlib import Path
import ast
SRC=(Path(__file__).resolve().parents[1]/"scripts/run_phase7_ensemble.py").read_text(encoding="utf-8")
def main():
    ast.parse(SRC)
    for token in ["P01","P10","0.10*len(v)","C=1.0","max_iter=500","random_state=SEED","<200","BLOCKED"]:
        assert token in SRC, token
    assert "decision_times.iloc" not in SRC
    print("Phase 7 regression checks PASS")
if __name__=="__main__": main()
