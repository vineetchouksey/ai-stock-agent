def calculate_rs(stock_df, index_df):
    # Align dates
    combined = stock_df[['Close']].join(
        index_df[['Close']], lsuffix='_stock', rsuffix='_index', how='inner'
    )

    # RS Ratio
    combined['rs'] = combined['Close_stock'] / combined['Close_index']

    # RS Moving Average
    combined['rs_ma'] = combined['rs'].rolling(50).mean()

    latest = combined.iloc[-1]

    # RS Trend
    if latest['rs'] > latest['rs_ma']:
        trend = "STRONG"
    else:
        trend = "WEAK"

    return {
        "rs_value": latest['rs'],
        "rs_ma": latest['rs_ma'],
        "rs_trend": trend
    }