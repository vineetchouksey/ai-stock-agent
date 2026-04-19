import yfinance as yf

# ✅ Add this function at TOP (below imports)
def normalize_dataframe(df):
    # Flatten multi-level columns (yfinance issue)
    if hasattr(df.columns, "levels"):
        df.columns = df.columns.get_level_values(0)

    # Ensure numeric types
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        if col in df.columns:
            df[col] = df[col].astype(float)

    return df


# ✅ Existing function (MODIFY this)
def fetch_stock_data(symbol):
    print(f"Fetching data for {symbol}...")
    
    df = yf.download(symbol, period="1y", interval="1d")

    if df.empty:
        raise ValueError(f"No data found for {symbol}")

    # 🔥 ADD THIS LINE HERE
    df = normalize_dataframe(df)

    df.dropna(inplace=True)
    
    return df

def fetch_nifty_data():
    df = yf.download("^NSEI", period="1y", interval="1d")

    df = normalize_dataframe(df)
    df.dropna(inplace=True)

    return df