def calculate_score(row):
    score = 0

    # --- Scanner strength ---
    if row["scanner_signal"] == "🚀 ELITE BUY":
        score += 50
    elif row["scanner_signal"] == "⚡ STRONG BREAKOUT":
        score += 30
    elif row["scanner_signal"] == "👀 WATCHLIST":
        score += 10

    # --- Relative Strength ---
    if row["rs_trend"] == "STRONG":
        score += 20

    # --- Volume + Breakout ---
    if row["volume_spike"]:
        score += 10
    if row["breakout"]:
        score += 15
    if row["dry_volume"]:
        score += 5

    # --- Bonus: Near 52W high ---
    if row["near_52w_high"]:
        score += 10

    return score


def rank_stocks(df):
    df["score"] = df.apply(calculate_score, axis=1)

    # Sort descending
    df = df.sort_values(by="score", ascending=False)

    return df