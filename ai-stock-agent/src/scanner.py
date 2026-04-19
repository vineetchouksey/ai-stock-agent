import pandas as pd

def analyze_stock(df):
    latest = df.iloc[-1]

    # --- 1. 52 WEEK HIGH ---
    high_52 = df['High'].rolling(252).max().iloc[-1]
    near_high = latest['Close'] >= 0.85 * high_52

    # --- 2. VOLUME DRY-UP ---
    avg_volume_20 = df['Volume'].rolling(20).mean().iloc[-1]
    low_volume_days = df['Volume'].iloc[-10:] < (0.5 * avg_volume_20)
    dry_volume = low_volume_days.sum() >= 5

    # --- 3. VOLUME SPIKE ---
    volume_spike = latest['Volume'] > 1.5 * avg_volume_20

    # --- 4. BREAKOUT ---
    recent_high = df['High'].iloc[-20:].max()
    breakout = latest['Close'] > recent_high

    return {
        "near_52w_high": near_high,
        "dry_volume": dry_volume,
        "volume_spike": volume_spike,
        "breakout": breakout
    }

def scanner_signal(flags, rs):
    if (
        flags["near_52w_high"] and
        flags["dry_volume"] and
        flags["volume_spike"] and
        flags["breakout"] and
        rs["rs_trend"] == "STRONG"
    ):
        return "🚀 ELITE BUY"

    elif (
        flags["breakout"] and
        flags["volume_spike"] and
        rs["rs_trend"] == "STRONG"
    ):
        return "⚡ STRONG BREAKOUT"

    elif flags["dry_volume"]:
        return "👀 WATCHLIST"

    else:
        return "❌ NO SIGNAL"