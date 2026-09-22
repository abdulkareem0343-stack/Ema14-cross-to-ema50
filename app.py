import streamlit as st
import ccxt
import pandas as pd
from ta.trend import EMAIndicator

# Page configuration
st.set_page_config(page_title="KuCoin EMA Gap Scanner", page_icon="📈", layout="wide")

st.title("📈 KuCoin EMA Gap & Cross Scanner")
st.caption("EMA 14 aur EMA 50 ke darmiyan gap wale Bullish aur Bearish coins ko alag alag scan karein.")

# Sidebar settings
st.sidebar.header("⚙️ Scanner Settings")
timeframe = st.sidebar.selectbox("Select Timeframe", ['5m', '15m', '1h', '4h', '1d'], index=2)
limit_coins = st.sidebar.slider("Number of Coins to Scan", min_value=50, max_value=600, value=300, step=50)

st.sidebar.markdown("---")
st.sidebar.header("🎯 Specific EMA Gap Filters")

# Filter 1: Dedicated EMA Gap Direction Filter
gap_direction_filter = st.sidebar.radio(
    "1️⃣ Select EMA Gap Direction",
    [
        "All Coins (Both Directions)",
        "🟢 EMA 14 > EMA 50 Only (Bullish Gap / Up Trend)",
        "🔴 EMA 50 > EMA 14 Only (Bearish Gap / Down Trend)"
    ]
)

# Filter 2: Min Gap Slider
min_gap = st.sidebar.slider(
    "2️⃣ Minimum EMA Gap Percentage (%)",
    min_value=0.0,
    max_value=15.0,
    value=0.2,
    step=0.1,
    help="Is se kam gap wale coins filter out ho jayenge."
)

# Filter 3: Gainer / Loser Filter
performance_filter = st.sidebar.selectbox(
    "3️⃣ Performance Filter",
    [
        "All Coins (Order by Largest Gap)",
        "🚀 Top Gainers First (% Change High to Low)",
        "📉 Top Losers First (% Change Low to High)"
    ]
)

# Fetch KuCoin USDT Pairs & 24h Ticker Data
@st.cache_data(ttl=300)
def get_kucoin_usdt_pairs(max_coins):
    try:
        exchange = ccxt.kucoin({'enableRateLimit': True})
        tickers = exchange.fetch_tickers()
        usdt_pairs = [
            symbol for symbol in tickers.keys() 
            if symbol.endswith('/USDT') and tickers[symbol].get('active', True)
        ]
        return usdt_pairs[:max_coins], tickers
    except Exception as e:
        st.error(f"Error fetching symbols from KuCoin: {e}")
        return [], {}

# Calculate EMA gap and details
def analyze_ema_gap(exchange, symbol, tf, ticker):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=100)
        if len(ohlcv) < 50:
            return None
            
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Calculate EMAs
        ema14_indicator = EMAIndicator(close=df['close'], window=14)
        ema50_indicator = EMAIndicator(close=df['close'], window=50)
        
        df['EMA14'] = ema14_indicator.ema_indicator()
        df['EMA50'] = ema50_indicator.ema_indicator()
        
        curr_ema14 = df['EMA14'].iloc[-1]
        curr_ema50 = df['EMA50'].iloc[-1]
        curr_price = df['close'].iloc[-1]
        
        # Percentage gap between EMA 14 and EMA 50
        gap_pct = abs((curr_ema14 - curr_ema50) / curr_ema50) * 100
        
        # Direction check
        if curr_ema14 > curr_ema50:
            direction = "🟢 EMA 14 Above EMA 50"
            is_bullish = True
        else:
            direction = "🔴 EMA 50 Above EMA 14"
            is_bullish = False
            
        # 24h Change %
        if ticker and 'percentage' in ticker and ticker['percentage'] is not None:
            price_change_pct = ticker['percentage']
        else:
            price_change_pct = ((curr_price - df['close'].iloc[-2]) / df['close'].iloc[-2]) * 100
            
        volume_24h = ticker.get('quoteVolume', df['volume'].iloc[-1] * curr_price) if ticker else df['volume'].iloc[-1] * curr_price
        
        return {
            "Symbol": symbol,
            "Price": curr_price,
            "EMA 14": curr_ema14,
            "EMA 50": curr_ema50,
            "EMA Gap %": round(gap_pct, 2),
            "Direction": direction,
            "Is_Bullish": is_bullish,
            "24h Change %": round(price_change_pct, 2),
            "Volume ($)": f"${volume_24h:,.0f}" if volume_24h else "$0"
        }
    except Exception:
        return None

# Render Cards View
def render_coin_cards(df_list):
    if df_list.empty:
        st.info("Is selected gap threshold par koi coin nahi mila.")
        return
        
    cols_per_row = 3
    cols = st.columns(cols_per_row)
    
    for idx, row in df_list.reset_index(drop=True).iterrows():
        col = cols[idx % cols_per_row]
        with col:
            border_color = "#10B981" if row['Is_Bullish'] else "#EF4444"
            bg_style = "rgba(16, 185, 129, 0.08)" if row['Is_Bullish'] else "rgba(239, 68, 68, 0.08)"
                
            with st.container():
                st.markdown(
                    f"""
                    <div style="border: 1px solid #374151; border-left: 5px solid {border_color}; 
                                background-color: {bg_style}; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
                        <div style="display:flex; justify-content: space-between; align-items:center;">
                            <h4 style="margin:0; padding:0;">{row['Symbol']}</h4>
                            <span style="background-color:{border_color}; color:#fff; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:bold;">
                                Gap: {row['EMA Gap %']}%
                            </span>
                        </div>
                        <p style="margin:4px 0 8px 0; font-size:12px; color:#9CA3AF;">{row['Direction']}</p>
                        <hr style="margin:4px 0 8px 0; border-color:#374151;">
                        <div style="display:flex; justify-content: space-between; font-size:13px;">
                            <span><b>Price:</b> ${row['Price']:,.4f}</span>
                            <span style="color:{'#10B981' if row['24h Change %'] >= 0 else '#EF4444'}"><b>24h Chg:</b> {row['24h Change %']}%</span>
                        </div>
                        <div style="display:flex; justify-content: space-between; font-size:12px; color:#D1D5DB; margin-top:4px;">
                            <span><b>EMA 14:</b> {row['EMA 14']:.4f}</span>
                            <span><b>EMA 50:</b> {row['EMA 50']:.4f}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

if st.button("🚀 Start Scanning KuCoin Gap", type="primary"):
    exchange = ccxt.kucoin({'enableRateLimit': True})
    symbols, tickers = get_kucoin_usdt_pairs(limit_coins)
    
    if not symbols:
        st.warning("No KuCoin pairs found.")
    else:
        st.info(f"Scanning top {len(symbols)} USDT pairs on KuCoin for EMA Gap...")
        progress_bar = st.progress(0)
        results = []
        
        for i, sym in enumerate(symbols):
            sym_ticker = tickers.get(sym, {})
            res = analyze_ema_gap(exchange, sym, timeframe, sym_ticker)
            if res:
                results.append(res)
            progress_bar.progress((i + 1) / len(symbols))
            
        df_results = pd.DataFrame(results)
        
        if not df_results.empty:
            filtered_df = df_results.copy()
            
            # Apply Minimum Gap Filter
            filtered_df = filtered_df[filtered_df['EMA Gap %'] >= min_gap]
            
            # Apply Direction Filter
            if gap_direction_filter == "🟢 EMA 14 > EMA 50 Only (Bullish Gap / Up Trend)":
                filtered_df = filtered_df[filtered_df['Is_Bullish'] == True]
            elif gap_direction_filter == "🔴 EMA 50 > EMA 14 Only (Bearish Gap / Down Trend)":
                filtered_df = filtered_df[filtered_df['Is_Bullish'] == False]
                
            # Apply Performance / Sort Order
            if performance_filter == "🚀 Top Gainers First (% Change High to Low)":
                filtered_df = filtered_df.sort_values(by='24h Change %', ascending=False)
            elif performance_filter == "📉 Top Losers First (% Change Low to High)":
                filtered_df = filtered_df.sort_values(by='24h Change %', ascending=True)
            else:
                filtered_df = filtered_df.sort_values(by='EMA Gap %', ascending=False)

            # Summary Metrics Bar
            bullish_count = len(df_results[df_results['Is_Bullish'] == True])
            bearish_count = len(df_results[df_results['Is_Bullish'] == False])
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Scanned", len(df_results))
            m2.metric("🟢 EMA 14 > EMA 50 Coins", bullish_count)
            m3.metric("🔴 EMA 50 > EMA 14 Coins", bearish_count)
            m4.metric("Matching Gap Results", len(filtered_df))
            
            st.write("---")
            
            # Display Options Tabs
            tab1, tab2 = st.tabs(["🎴 Cards View", "📋 Complete Table View"])
            
            with tab1:
                st.subheader(f"Filtered Results ({len(filtered_df)} Coins Found)")
                render_coin_cards(filtered_df)
                
            with tab2:
                st.subheader("📋 Detailed Data Table")
                st.dataframe(filtered_df, use_container_width=True)
