import numpy as np, pandas as pd
from run_phase5_family_d import sequence_features, model, fit_predict_block

def main():
    rng=np.random.default_rng(42)
    X=pd.DataFrame(rng.normal(size=(80,7)))
    y=pd.Series((rng.random(80)>0.5).astype(int))
    # deterministic sequence construction and session-local shape
    a,i=sequence_features(X,20,"lag")
    b,j=sequence_features(X,20,"lag")
    assert np.array_equal(a,b) and np.array_equal(i,j)
    assert a.shape[0]==61 and a.shape[1]==140
    for name in ["D01","D02","D03","D04","D05","D06","D08","D09","D10","D11","D12"]:
        p=fit_predict_block(name,X,y,50,np.array([50,51]))
        assert len(p)==2
        assert np.all(np.isfinite(p)) and np.all((p>=0)&(p<=1))
    print("PHASE5_REGRESSION_PASS")
if __name__=="__main__": main()
