import ta

def apply_indicators(df):
    close = df['Close'].squeeze()  # 🔥 ensures 1D
    
    df['rsi'] = ta.momentum.RSIIndicator(close).rsi()
    
    macd = ta.trend.MACD(close)
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    
    df['ema_50'] = ta.trend.EMAIndicator(close, window=50).ema_indicator()
    df['ema_200'] = ta.trend.EMAIndicator(close, window=200).ema_indicator()
    
    return df