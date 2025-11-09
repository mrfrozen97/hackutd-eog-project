import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt

def detect_long_term_trend_changes(timestamps, values,
                                   smooth_window=31,    # must be odd
                                   polyorder=2,
                                   min_persist_minutes=30,
                                   slope_smooth_window=11,
                                   slope_threshold=1e-3):
    import numpy as np
    import pandas as pd
    from scipy.signal import savgol_filter

    t = pd.to_datetime(timestamps)
    vals = np.asarray(values, dtype=float)
    n = len(vals)
    if n < max(smooth_window, slope_smooth_window) + 2:
        raise ValueError("series too short for chosen smoothing windows")

    def _odd(x):
        return int(x) if int(x) % 2 == 1 else int(x) + 1
    sw = min(_odd(smooth_window), n-1)
    if sw % 2 == 0: sw -= 1
    sw = max(3, sw)
    sg = savgol_filter(vals, window_length=sw, polyorder=polyorder, mode='interp')

    dt_seconds = np.gradient(t.astype(np.int64) // 10**9)
    ds = np.gradient(sg) / (dt_seconds + 1e-9)
    ds_per_min = ds * 60.0

    ssw = min(_odd(slope_smooth_window), n-1)
    if ssw % 2 == 0: ssw -= 1
    ssw = max(3, ssw)
    slope_sm = savgol_filter(ds_per_min, window_length=ssw, polyorder=1, mode='interp')

    sign = np.zeros_like(slope_sm, dtype=int)
    sign[slope_sm > slope_threshold] = 1
    sign[slope_sm < -slope_threshold] = -1

    change_idxs = np.where(np.diff(sign) != 0)[0] + 1

    accepted_changes = []
    min_persist_samples = int(np.round(min_persist_minutes))
    for idx in change_idxs:
        new_sign = sign[idx]
        if new_sign == 0:
            continue
        j = idx
        while j < n and sign[j] == new_sign:
            j += 1
        persist = j - idx
        if persist >= min_persist_samples:
            accepted_changes.append({
                "index": idx,
                "timestamp": t.iloc[idx],
                "new_sign": int(new_sign),
                "persist_samples": persist,
                "slope_at_change": float(slope_sm[idx])
            })

    return {
        "smoothed": sg,
        "slope_per_min": slope_sm,
        "sign": sign,
        "candidates": accepted_changes
    }
