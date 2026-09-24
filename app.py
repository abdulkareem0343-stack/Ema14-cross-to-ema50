import streamlit as st
import ccxt
import pandas as pd
import ta

# Page Layout Setup
st.set_page_config(page_title="Crypto EMA Scanner", layout="wide")
st.title(" Crypto EMA 100 Multi-Exchange Scanner")

# --- SIDEBAR FILTERS ---
st.sidebar.header(" Filter Options")

# 1. Exchange Select Box (Binance & Bybit removed)
selected_exchanges = st.sidebar.multiselect(
    "Select Exchanges:",
    options=["kucoin", "okx"],
    default=["kucoin", "okx"]
)

# 2. Timeframe Selection
timeframe = st.sidebar.selectbox(
    "Select Timeframe:",
    options=["1m", "5m", "15m", "1h", "4h", "1d"],
    index=1  # Default 5m
)

# 3. Coin Find Limit
coin_limit = st.sidebar.slider(
    "Coins Limit Per Exchange:",
    min_value=10,
    max_value=1000,
    value=100,
    step=10
)

# 4. EMA Gap (Threshold %)
threshold_percent = st.sidebar.slider(
    "EMA Gap / Tolerance (%):",
    min_value=0.05,
    max_value=5.0,
    value=0.3,
    step=0.05,
    help="Candle price EMA100 ke kitni nazdeek ho (e.g. 0.3% gap)"
)

EMA_PERIOD = 100

# Function to initialize selected exchanges
def get_exchange_instances(selected_names):
    instances = {}
    for name in selected_names:
        if name == 'kucoin':
            instances['kucoin'] = ccxt.kucoin({'enableRateLimit': True})
        elif name == 'okx':
            instances['okx'] = ccxt.okx({'enableRateLimit': True})
    return instances

# --- MAIN SCANNER LOGIC ---
if st.button("Scan Market"):
    if not selected_exchanges:
        st.warning("Barah-e-karam kam se kam ek Exchange select karein!")
    else:
        exchanges = get_exchange_instances(selected_exchanges)
        matched_coins = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        total_exchanges = len(exchanges)
        
        for ex_index, (ex_name, ex_obj) in enumerate(exchanges.items()):
            status_text.text(f"Scanning {ex_name.upper()}...")
            try:
                markets = ex_obj.load_markets()
                # USDT Pairs filter kar ke user limit apply karna
                symbols = [s for s in markets if s.endswith('/USDT')][:coin_limit]
                
                for i, symbol in enumerate(symbols):
                    try:
                        ohlcv = ex_obj.fetch_ohlcv(symbol, timeframe=timeframe, limit=150)
                        if len(ohlcv) < EMA_PERIOD:
                            continue
                        
                        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                        
                        # EMA 100 calculation
                        df['ema100'] = ta.trend.ema_indicator(df['close'], window=EMA_PERIOD)
                        
                        last_candle = df.iloc[-1]
                        close_price = last_candle['close']
                        ema100 = last_candle['ema100']
                        
                        if pd.isna(ema100):
                            continue
                            
                        # Percent difference calculation
                        diff_percent = abs(close_price - ema100) / ema100 * 100
                        
                        if diff_percent <= threshold_percent:
                            matched_coins.append({
                                'Exchange': ex_name.upper(),
                                'Symbol': symbol,
                                'Price ($)': close_price,
                                'EMA 100': round(ema100, 4),
                                'Gap (%)': round(diff_percent, 2),
                                'Timeframe': timeframe
                            })
                    except Exception:
                        continue
                        
            except Exception as e:
                st.error(f"Error loading {ex_name}: {e}")
            
            # Update progress bar
            progress_bar.progress((ex_index + 1) / total_exchanges)

        status_text.text("Scan Complete!")

        # Results Display
        if matched_coins:
            st.success(f"Total {len(matched_coins)} Coins found matching criteria!")
            result_df = pd.DataFrame(matched_coins)
            st.dataframe(result_df, use_container_width=True)
        else:
            st.warning(" Koi coin nahi mila jo is criteria par pura utarta ho. Sidebar se Gap (%) ya Limit barha kar dekhein.")
