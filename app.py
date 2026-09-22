import streamlit as st
import ccxt
import pandas as pd
from ta.trend import EMAIndicator

# Page configuration
st.set_page_config(page_title="KuCoin EMA & Gainers/Losers Scanner", page_icon="📈", layout="wide")

st.title("📈 KuCoin Advance EMA Scanner")
st.caption("Bullish/Bearish Crosses aur Top Gainers/Losers ke independent alag filters ke sath live market scan karein.")

# Sidebar settings
st.sidebar.header("⚙️ Scanner Settings")
timeframe = st.sidebar.selectbox("Select Timeframe", ['5m', '15m', '1h', '4h', '1d'], index=2)
limit_coins = st.sidebar.slider("Number of Coins to Scan", min_value=50, max_value=600, value=300, step=50)

st.sidebar.markdown("---")
st.sidebar.header("🎯 Independent Filters")

# Filter 1: Crossover Filter
signal_filter = st.sidebar.selectbox(
    "1️⃣ Signal / Cross Filter",
    [
        "All Signals",
        "🟢 Bullish Cross Only (EMA 14 > EMA 50)",
        "🔴 Bearish Cross Only (EMA 50 > EMA 14)",
        "⚪ No Cross Only"
    ]
)

# Filter 2: Gainer / Loser Filter
performance_filter = st.sidebar.selectbox(
    "2️⃣ Gainer / Loser Filter",
    [
        "All Coins (Normal Order)",
        "🚀 Top Gainers Only (% Change High to Low)",
        "📉 Top Losers Only (% Change Low to High)"
    ]
)

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
        
        # Calculate EMAs
        ema14_indicator = EMAIndicator(close=df['close'], window=14)
        ema50_indicator = EMAIndicator(close=df['close'], window=50)
        
        df['EMA14'] = ema14_indicator.ema_indicator()
        df['EMA50'] = ema50_indicator.ema_indicator()
        
        prev_ema14 = df['EMA14'].iloc[-2]
        prev_ema50 = df['EMA50'].iloc[-2]
        curr_ema14 = df['EMA14'].iloc[-1]
        curr_ema50 = df['EMA50'].iloc[-1]
        curr_price = df['close'].iloc[-1]
        volume_24h = df['volume'].iloc[-1] * curr_price
        
        # Calculate 24h / candle change %
        price_change_pct = ((curr_price - df['close'].iloc[-2]) / df['close'].iloc[-2]) * 100
        ema_gap = ((curr_ema14 - curr_ema50) / curr_ema50) * 100
        
        status = "NO CROSS"
        cross_type = "None"
        
        if prev_ema14 <= prev_ema50 and curr_ema14 > curr_ema50:
            status = "🟢 BULLISH CROSS (EMA 14 > EMA 50)"
            cross_type = "Bullish"
        elif prev_ema14 >= prev_ema50 and curr_ema14 < curr_ema50:
            status = "🔴 BEARISH CROSS (EMA 50 > EMA 14)"
            cross_type = "Bearish"
            
        return {
            "Symbol": symbol,
            "Price": curr_price,
            "EMA 14": curr_ema14,
            "EMA 50": curr_ema50,
            "Gap %": round(ema_gap, 2),
            "Change %": round(price_change_pct, 2),
            "Volume ($)": f"${volume_24h:,.0f}",
            "Status": status,
            "Cross Type": cross_type
        }
    except Exception:
        return None

# Render Advance Cards Layout
def render_coin_cards(df_list):
    if df_list.empty:
        st.info("Koi coin is selection mein nahi mila.")
        return
        
    cols_per_row = 3
    cols = st.columns(cols_per_row)
    
    for idx, row in df_list.reset_index(drop=True).iterrows():
        col = cols[idx % cols_per_row]
        with col:
            if row['Cross Type'] == 'Bullish':
                border_color = "#10B981"
                bg_style = "rgba(16, 185, 129, 0.1)"
            elif row['Cross Type'] == 'Bearish':
                border_color = "#EF4444"
                bg_style = "rgba(239, 68, 68, 0.1)"
            else:
                border_color = "#6B7280"
                bg_style = "rgba(107, 114, 128, 0.05)"
                
            with st.container():
                st.markdown(
                    f"""
                    <div style="border: 1px solid #374151; border-left: 5px solid {border_color}; 
                                background-color: {bg_style}; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
                        <h4 style="margin:0; padding:0;">{row['Symbol']}</h4>
                        <p style="margin:2px 0 8px 0; font-size:12px; color:#9CA3AF;">{row['Status']}</p>
                        <hr style="margin:4px 0 8px 0; border-color:#374151;">
                        <div style="display:flex; justify-content: space-between; font-size:13px;">
                            <span><b>Price:</b> ${row['Price']:,.4f}</span>
                            <span style="color:{'#10B981' if row['Change %'] >= 0 else '#EF4444'}"><b>Chg:</b> {row['Change %']}%</span>
                        </div>
                        <div style="display:flex; justify-content: space-between; font-size:12px; color:#D1D5DB; margin-top:4px;">
                            <span><b>EMA 14:</b> {row['EMA 14']:.4f}</span>
                            <span><b>EMA 50:</b> {row['EMA 50']:.4f}</span>
                        </div>
                        <div style="display:flex; justify-content: space-between; font-size:11px; color:#9CA3AF; margin-top:4px;">
                            <span><b>EMA Gap:</b> {row['Gap %']}%</span>
                            <span><b>Vol:</b> {row['Volume ($)']}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

if st.button("🚀 Start Scanning KuCoin", type="primary"):
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
            filtered_df = df_results.copy()
            
            # Apply 1: Signal Filter
            if signal_filter == "🟢 Bullish Cross Only (EMA 14 > EMA 50)":
                filtered_df = filtered_df[filtered_df['Cross Type'] == 'Bullish']
            elif signal_filter == "🔴 Bearish Cross Only (EMA 50 > EMA 14)":
                filtered_df = filtered_df[filtered_df['Cross Type'] == 'Bearish']
            elif signal_filter == "⚪ No Cross Only":
                filtered_df = filtered_df[filtered_df['Cross Type'] == 'None']
                
            # Apply 2: Gainer / Loser Filter
            if performance_filter == "🚀 Top Gainers Only (% Change High to Low)":
                filtered_df = filtered_df.sort_values(by='Change %', ascending=False)
            elif performance_filter == "📉 Top Losers Only (% Change Low to High)":
                filtered_df = filtered_df.sort_values(by='Change %', ascending=True)
            else:
                # Default sorting by Gap % (Lowest to Highest)
                filtered_df = filtered_df.sort_values(by='Gap %', ascending=True)

            # Summary Metrics Bar
            bullish_count = len(df_results[df_results['Cross Type'] == 'Bullish'])
            bearish_count = len(df_results[df_results['Cross Type'] == 'Bearish'])
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Scanned", len(df_results))
            m2.metric("🟢 Bullish Crosses", bullish_count)
            m3.metric("🔴 Bearish Crosses", bearish_count)
            m4.metric("Matching Filter Results", len(filtered_df))
            
            st.write("---")
            
            # Display Options Tabs
            tab1, tab2 = st.tabs(["🎴 Advance Cards View", "📋 Complete Table View"])
            
            with tab1:
                st.subheader(f"Results ({len(filtered_df)} Coins Found)")
                render_coin_cards(filtered_df)
                
            with tab2:
                st.subheader("📋 Table View (Sorted as per selection)")
                st.dataframe(filtered_df, use_container_width=True)
