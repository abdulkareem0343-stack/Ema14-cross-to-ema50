import streamlit as st
import ccxt
import pandas as pd
from ta.trend import EMAIndicator

# Page configuration
st.set_page_config(page_title="KuCoin EMA Crossover Scanner", page_icon="📈", layout="wide")

st.title("📈 KuCoin EMA 14 / EMA 50 Crossover Scanner")
st.write("KuCoin ke sabhi Top USDT pairs (up to 600) par live EMA 14 aur EMA 50 crossover detect karein.")

# Sidebar settings
st.sidebar.header("Settings")
timeframe = st.sidebar.selectbox("Select Timeframe", ['5m', '15m', '1h', '4h', '1d'], index=2)
limit_coins = st.sidebar.slider("Number of Coins to Scan", min_value=50, max_value=600, value=300, step=50)

# Fetch KuCoin USDT Pairs Dynamically
@st.cache_data(ttl=3600)
def get_kucoin_usdt_pairs(max_coins):
    try:
        exchange = ccxt.kucoin({'enableRateLimit': True})
        markets = exchange.load_markets()
        usdt_pairs = [
            symbol for symbol in markets.keys() 
            if symbol.endswith('/USDT') and markets[symbol]['active']
        ]
        return usdt_pairs[:max_coins]
    except Exception as e:
        st.error(f"Error fetching symbols from KuCoin: {e}")
        return []

# Function to calculate EMA and detect cross
def check_ema_cross(exchange, symbol, tf):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=100)
        if len(ohlcv) < 50:
            return None
            
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Calculate EMAs using 'ta' library
        ema14_indicator = EMAIndicator(close=df['close'], window=14)
        ema50_indicator = EMAIndicator(close=df['close'], window=50)
        
        df['EMA14'] = ema14_indicator.ema_indicator()
        df['EMA50'] = ema50_indicator.ema_indicator()
        
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
            
        # Only return items if there's useful info, or for all
        return {
            "Symbol": symbol,
            "Price": f"${curr_price:,.4f}",
            "EMA 14": round(curr_ema14, 4),
            "EMA 50": round(curr_ema50, 4),
            "Status": status
        }
    except Exception:
        return None

if st.button("🚀 Start Scanning KuCoin"):
    exchange = ccxt.kucoin({'enableRateLimit': True})
    symbols = get_kucoin_usdt_pairs(limit_coins)
    
    if not symbols:
        st.warning("No KuCoin pairs found.")
    else:
        st.info(f"Scanning top {len(symbols)} USDT pairs on KuCoin...")
        progress_bar = st.progress(0)
        results = []
        
        for i, sym in enumerate(symbols):
            res = check_ema_cross(exchange, sym, timeframe)
            if res:
                results.append(res)
            progress_bar.progress((i + 1) / len(symbols))
            
        df_results = pd.DataFrame(results)
        
        if not df_results.empty:
            # Filter only crossovers by default
            crossovers_only = df_results[df_results['Status'] != 'NO CROSS']
            
            st.subheader(f"⚡ Crossovers Found ({timeframe})")
            if not crossovers_only.empty:
                st.dataframe(crossovers_only, use_container_width=True)
            else:
                st.info("Filhal kisi coin par fresh crossover nahi mila.")
                
            with st.expander("Show All Scanned Coins"):
                st.dataframe(df_results, use_container_width=True)
