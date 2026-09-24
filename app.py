import streamlit as st
import ccxt
import pandas as pd
import ta  # pandas-ta ki jagah 'ta' import karein

st.title("Crypto EMA 100 Scanner")

TIMEFRAME = '5m'
EMA_PERIOD = 100
THRESHOLD_PERCENT = 0.3

exchanges = {
    'binance': ccxt.binance({'enableRateLimit': True}),
    'bybit': ccxt.bybit({'enableRateLimit': True}),
    'kucoin': ccxt.kucoin({'enableRateLimit': True}),
    'okx': ccxt.okx({'enableRateLimit': True})
}

if st.button("Scan Coins"):
    matched_coins = []
    
    for ex_name, ex_obj in exchanges.items():
        st.write(f"Scanning {ex_name.upper()}...")
        try:
            markets = ex_obj.load_markets()
            symbols = [s for s in markets if s.endswith('/USDT')][:100] # Rate limit se bachne ke liye initial limit
            
            for symbol in symbols:
                try:
                    ohlcv = ex_obj.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=150)
                    if len(ohlcv) < EMA_PERIOD:
                        continue
                    
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    
                    # 'ta' library se EMA calculate karna
                    df['ema100'] = ta.trend.ema_indicator(df['close'], window=EMA_PERIOD)
                    
                    last_candle = df.iloc[-1]
                    close_price = last_candle['close']
                    ema100 = last_candle['ema100']
                    
                    if pd.isna(ema100):
                        continue
                        
                    diff_percent = abs(close_price - ema100) / ema100 * 100
                    
                    if diff_percent <= THRESHOLD_PERCENT:
                        matched_coins.append({
                            'Exchange': ex_name.upper(),
                            'Symbol': symbol,
                            'Price': close_price,
                            'EMA 100': round(ema100, 4),
                            'Diff (%)': round(diff_percent, 2)
                        })
                except Exception:
                    continue
        except Exception as e:
            st.error(f"Error loading {ex_name}: {e}")

    if matched_coins:
        st.success(f"Found {len(matched_coins)} coins near EMA 100!")
        st.dataframe(pd.DataFrame(matched_coins))
    else:
        st.warning("No coins found matching criteria.")
