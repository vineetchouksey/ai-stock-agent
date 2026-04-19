def generate_signal(df, fundamentals):
    latest = df.iloc[-1]

    # Technical rules
    if latest['rsi'] < 30 and latest['macd'] > latest['macd_signal']:
        tech = "BUY"
    elif latest['rsi'] > 70:
        tech = "SELL"
    else:
        tech = "HOLD"

    # Fundamental rules
    if fundamentals["pe"] and fundamentals["pe"] < 25:
        fund = "GOOD"
    else:
        fund = "WEAK"

    # Final decision
    if tech == "BUY" and fund == "GOOD":
        return "STRONG BUY"
    elif tech == "SELL":
        return "SELL"
    else:
        return "HOLD"