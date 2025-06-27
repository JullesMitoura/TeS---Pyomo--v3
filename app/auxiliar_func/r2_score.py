import pandas as pd
import numpy as np

def calculate_r2(y_true, y_pred):
    y_true = pd.Series(y_true).reset_index(drop=True)
    y_pred = pd.Series(y_pred).reset_index(drop=True)
    
    valid_indices = y_true.notna() & y_pred.notna()
    y_true_clean = y_true[valid_indices]
    y_pred_clean = y_pred[valid_indices]
    
    if len(y_true_clean) < 2:
        return np.nan
    mean_y_true = y_true_clean.mean()

    ss_tot = ((y_true_clean - mean_y_true) ** 2).sum()

    if ss_tot == 0:
        return 1.0 if ((y_true_clean - y_pred_clean) ** 2).sum() == 0 else np.nan
    ss_res = ((y_true_clean - y_pred_clean) ** 2).sum()
    r2 = 1 - (ss_res / ss_tot)
    return r2