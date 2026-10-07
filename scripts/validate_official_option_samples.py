from __future__ import annotations
from pathlib import Path
import csv
import io
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "cache" / "raw" / "nse_fno_samples"

LEGACY = {
    "INSTRUMENT","SYMBOL","EXPIRY_DT","STRIKE_PR","OPTION_TYP",
    "OPEN","HIGH","LOW","CLOSE","SETTLE_PR","CONTRACTS","OPEN_INT"
}
UDIFF = {
    "FinInstrmTp","TckrSymb","XpryDt","StrkPric","OptnTp",
    "OpnPric","HghPric","LwPric","ClsPric","OpnIntrst"
}
def sample_headers(z: zipfile.ZipFile):
    names=[n for n in z.namelist() if n.lower().endswith((".csv",".txt"))]
    if not names:
        raise ValueError("zip contains no CSV/TXT file")
    with z.open(names[0]) as fh:
        data=fh.read(65536)
    text=data.decode("utf-8-sig", errors="replace")
    return [h.strip() for h in next(csv.reader(io.StringIO(text)))]

checks=[
    ("2024-07-05_legacy.zip","legacy"),
    ("2024-07-08_udiff.zip","udiff"),
]
for name, kind in checks:
    path=RAW/name
    if not path.exists() or path.stat().st_size == 0:
        raise SystemExit(f"ERROR: missing archive {name}")
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None:
            raise SystemExit(f"ERROR: corrupt zip {name}")
        headers=set(sample_headers(z))
    required = LEGACY if kind=="legacy" else UDIFF
    missing=sorted(required-headers)
    if missing:
        raise SystemExit(f"ERROR: {name} missing expected schema fields: {missing}")
    print(f"PASS: {name} contains expected {kind} fields")
