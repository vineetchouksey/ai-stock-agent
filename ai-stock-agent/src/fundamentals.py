import yfinance as yf

def fetch_fundamentals(symbol):
    stock = yf.Ticker(symbol)
    info = stock.info

    return {
        "pe": info.get("trailingPE"),
        "roe": info.get("returnOnEquity"),
        "debt_to_equity": info.get("debtToEquity"),
        "revenue_growth": info.get("revenueGrowth")
    }