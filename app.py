import ccxt
import pandas as pd
import pandas_ta as ta
import time

# Multiple Exchanges Initialized
exchanges = {
    'binance': ccxt.binance({'enableRateLimit': True}),
    'bybit': ccxt.bybit({'enableRateLimit': True}),
    'kucoin': ccxt.kucoin({'enableRateLimit': True}),
    'okx': ccxt.okx({'enableRateLimit': True})
}

TIMEFRAME = '5m'
EMA_PERIOD = 100
THRESHOLD_PERCENT = 0.3  # Candle EMA100 sekitni nazdeek ho (0.3% range)

def fetch_and_scan(exchange_name, exchange_obj):
    print(f"\n--- Scanning Exchange: {exchange_name.upper()} ---")
    matched_coins = []
    
    try:
        markets = exchange_obj.load_markets()
        # USDT pairs filter kar rahe hain
        symbols = [s for s in markets if s.endswith('/USDT') or s.endswith('/USDT:USDT')][:300] 
        
        for symbol in symbols:
            try:
                # 5 minute ki candles fetch karna
                ohlcv = exchange_obj.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=150)
                if len(ohlcv) < EMA_PERIOD:
                    continue
                
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                
                # EMA 100 calculate karna
                df['ema100'] = ta.ema(df['close'], length=EMA_PERIOD)
                
                last_candle = df.iloc[-1]
                close_price = last_candle['close']
                ema100 = last_candle['ema100']
                
                # EMA 100 ke kitna nazdeek hai calculate karna
                diff_percent = abs(close_price - ema100) / ema100 * 100
                
                if diff_percent <= THRESHOLD_PERCENT:
                    matched_coins.append({
                        'Exchange': exchange_name.upper(),
                        'Symbol': symbol,
                        'Close Price': close_price,
                        'EMA 100': round(ema100, 4),
                        'Diff (%)': round(diff_percent, 2)
                    })
                    print(f" MATCH FOUND: {symbol} | Price: {close_price} | EMA100: {round(ema100, 4)} | Diff: {round(diff_percent, 2)}%")
            
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"Error fetching data from {exchange_name}: {e}")
        
    return matched_coins

# Execution
all_matches = []
for ex_name, ex_obj in exchanges.items():
    results = fetch_and_scan(ex_name, ex_obj)
    all_matches.extend(results)

print(f"\nTotal Coins Found Near EMA 100: {len(all_matches)}")
