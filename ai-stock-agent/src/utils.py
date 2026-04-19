def load_symbols_from_txt(file_path):
    with open(file_path, "r") as file:
        content = file.read()

    # Split by comma
    raw_symbols = content.split(",")

    cleaned_symbols = []

    for symbol in raw_symbols:
        symbol = symbol.strip()

        # Remove NSE: prefix
        if symbol.startswith("NSE:"):
            symbol = symbol.replace("NSE:", "")

        # Convert to yfinance format
        symbol = symbol + ".NS"

        cleaned_symbols.append(symbol)

    return cleaned_symbols

def load_symbols_from_csv(file_path):
    import pandas as pd

    df = pd.read_csv(file_path)

    # 🔥 Normalize column names (case-insensitive + trim)
    df.columns = [col.strip().lower() for col in df.columns]

    if "symbol" not in df.columns:
        raise ValueError("CSV must contain 'symbol' column (case-insensitive)")

    raw_symbols = df["symbol"].dropna().tolist()

    cleaned_symbols = []

    for symbol in raw_symbols:
        symbol = str(symbol).strip()

        # Remove NSE: prefix if present
        if symbol.startswith("NSE:"):
            symbol = symbol.replace("NSE:", "")

        # Add .NS if missing
        if not symbol.endswith(".NS"):
            symbol = symbol + ".NS"

        cleaned_symbols.append(symbol)

    return cleaned_symbols 

def load_symbols(source="txt"):
    if source == "txt":
        return load_symbols_from_txt("../data/stocks.txt")

    elif source == "csv":
        return load_symbols_from_csv("../data/stocks.csv")

    else:
        raise ValueError("Invalid source. Use 'txt' or 'csv'")

def normalize_symbol(symbol):
    symbol = str(symbol).strip()

    if symbol.startswith("NSE:"):
        symbol = symbol.replace("NSE:", "")

    if not symbol.endswith(".NS"):
        symbol = symbol + ".NS"

    return symbol