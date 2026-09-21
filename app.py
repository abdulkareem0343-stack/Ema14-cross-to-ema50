import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta

# Page configuration
st.set_page_config(page_title="EMA Crossover Scanner", page_icon="📈", layout="wide")

st.title("📈 Crypto EMA 14 / EMA 50 Crossover Scanner")
st.write("Binance ke top pairs par EMA 14 aur EMA 50 ka live crossover detect karein.")

# Sidebar settings
st.sidebar.header("Settings")
timeframe = st.sidebar.selectbox("Select Timeframe", ['5m', '15m', '1h', '4h', '1d'], index=2)

symbols = [
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT',
    'ADA/USDT', 'DOGE/USDT', 'AVAX/USDT', 'LINK/USDT', 'MATIC/USDT'
]

# Function to calculate EMA and detect cross
def check_ema_cross(symbol, tf):
    try:
        exchange = ccxt.binance({'enableRateLimit': True})
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Calculate EMAs
        df['EMA14'] = ta.ema(df['close'], length=14)
        df['EMA50'] = ta.ema(df['close'], length=50)
        
        prev_ema14 = df['EMA14'].iloc[-2]
        prev_ema50 = df['EMA50'].iloc[-2]
        curr_ema14 = df['EMA14'].iloc[-1]
        curr_ema50 = df['EMA50'].iloc[-1]
        curr_price = df['close'].iloc[-1]
        
        status = "NO CROSS"
        if prev_ema14 <= prev_ema50 and curr_ema14 > curr_ema50:
            status = "🟢 BULLISH CROSS"
        elif prev_ema14 >= prev_ema50 and curr_ema14 < curr_ema50:
            status = "🔴 BEARISH CROSS"
            
        return {
            "Symbol": symbol,
            "Price": f"${curr_price:,.4f}",
            "EMA 14": round(curr_ema14, 4),
            "EMA 50": round(curr_ema50, 4),
            "Status": status
        }
    except Exception as e:
        return {"Symbol": symbol, "Price": "Error", "EMA 14": "-", "EMA 50": "-", "Status": "Failed"}

if st.button("🚀 Start Scanning"):
    with st.spinner("Scanning Binance Market..."):
        results = []
        for sym in symbols:
            res = check_ema_cross(sym, timeframe)
            results.append(res)
            
        df_results = pd.DataFrame(results)
        
        # Highlight Crossovers
        st.subheader(f"Scan Results ({timeframe} Timeframe)")
        st.dataframe(df_results, use_container_width=True)
        
        # Summary
        bullish = df_results[df_results['Status'] == '🟢 BULLISH CROSS']
        bearish = df_results[df_results['Status'] == '🔴 BEARISH CROSS']
        
        if not bullish.empty:
            st.success(f"Bullish Cross Found: {', '.join(bullish['Symbol'].tolist())}")
        if not bearish.empty:
            st.error(f"Bearish Cross Found: {', '.join(bearish['Symbol'].tolist())}")
