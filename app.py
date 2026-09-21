import ccxt
import pandas as pd
import pandas_ta as ta

# Exchange initialize karein (Binance)
exchange = ccxt.binance()

# Jin coins ko scan karna hai (e.g. USDT pairs)
symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT']

def check_ema_cross(symbol, timeframe='1h'):
    try:
        # Candlestick data fetch karein
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # EMA 14 aur EMA 50 calculate karein
        df['EMA14'] = ta.ema(df['close'], length=14)
        df['EMA50'] = ta.ema(df['close'], length=50)
        
        # Last two candles check karein
        prev_ema14 = df['EMA14'].iloc[-2]
        prev_ema50 = df['EMA50'].iloc[-2]
        
        curr_ema14 = df['EMA14'].iloc[-1]
        curr_ema50 = df['EMA50'].iloc[-1]
        
        # Golden Cross (Bullish): EMA14 crosses ABOVE EMA50
        if prev_ema14 <= prev_ema50 and curr_ema14 > curr_ema50:
            print(f"🟢 [BULLISH CROSS] {symbol} par EMA 14 ne EMA 50 ko uper cross kiya!")
            
        # Death Cross (Bearish): EMA14 crosses BELOW EMA50
        elif prev_ema14 >= prev_ema50 and curr_ema14 < curr_ema50:
            print(f"🔴 [BEARISH CROSS] {symbol} par EMA 14 ne EMA 50 ko neeche cross kiya!")

    except Exception as e:
        print(f"Error checking {symbol}: {e}")

# Scan run karein
print("Scanning Market for EMA 14 / EMA 50 Crossover...\n")
for symbol in symbols:
    check_ema_cross(symbol, timeframe='1h')
  
