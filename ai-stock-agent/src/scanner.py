import pandas as pd

def analyze_stock(df):
    latest = df.iloc[-1]

    # ================================
    # 1. NEAR 52 WEEK HIGH
    # ================================
    high_52 = df['High'].rolling(252).max().iloc[-1]
    near_high = latest['Close'] >= 0.85 * high_52


    # ================================
    # 2. CONSOLIDATION (HORIZONTAL RANGE)
    # ================================
    lookback = 20
    recent_high = df['High'].iloc[-lookback:].max()
    recent_low = df['Low'].iloc[-lookback:].min()

    range_pct = (recent_high - recent_low) / recent_low

    # Tight range = consolidation
    tight_range = range_pct < 0.08   # 8% range


    # ================================
    # 3. NEAR RESISTANCE (NOT BROKEN YET)
    # ================================
    not_breakout = latest['Close'] <= recent_high
    near_resistance = latest['Close'] >= 0.95 * recent_high and not_breakout


    # ================================
    # 4. VOLUME DRY-UP
    # ================================
    avg_volume_20 = df['Volume'].rolling(20).mean().iloc[-1]

    recent_volumes = df['Volume'].iloc[-10:]
    dry_days = recent_volumes < (0.6 * avg_volume_20)

    volume_dry = dry_days.sum() >= 5


    return {
        "near_52w_high": near_high,
        "tight_consolidation": tight_range,
        "near_resistance": near_resistance,
        "dry_volume": volume_dry
    }

def scanner_signal(flags, rs):
    if (
        flags["near_52w_high"] and
        flags["tight_consolidation"] and
        flags["near_resistance"] and
        flags["dry_volume"] and
        rs["rs_trend"] == "STRONG"
    ):
        return "🎯 PRE-BREAKOUT"

    elif (
        flags["tight_consolidation"] and
        flags["dry_volume"]
    ):
        return "👀 BASE FORMING"

    else:
        return "❌ NO SETUP"
