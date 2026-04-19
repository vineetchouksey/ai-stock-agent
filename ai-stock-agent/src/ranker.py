def calculate_score(row):
    score = 0

    # --- Scanner strength ---
    if row["scanner_signal"] == "🎯 PRE-BREAKOUT":
        score += 50
    elif row["scanner_signal"] == "👀 BASE FORMING":
        score += 25

    # --- Relative Strength ---
    if row["rs_trend"] == "STRONG":
        score += 20

    # --- Structure quality ---
    if row["tight_consolidation"]:
        score += 15

    if row["near_resistance"]:
        score += 10

    if row["dry_volume"]:
        score += 10

    if row["near_52w_high"]:
        score += 10

    return score


def rank_stocks(df):
    df["score"] = df.apply(calculate_score, axis=1)

    # Sort descending
    df = df.sort_values(by="score", ascending=False)

    return df