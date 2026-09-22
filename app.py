import streamlit as st
import ccxt
import pandas as pd
from ta.trend import EMAIndicator

# Page configuration
st.set_page_config(page_title="KuCoin EMA & Gainers/Losers Scanner", page_icon="📈", layout="wide")

st.title("📈 KuCoin Advance EMA Scanner")
st.caption("Custom EMA position, fresh crossovers, and Gainers/Losers filters.")

# Sidebar settings
st.sidebar.header("⚙️ Scanner Settings")
timeframe = st.sidebar.selectbox("Select Timeframe", ['5m', '15m', '1h', '4h', '1d'], index=2)
limit_coins = st.sidebar.slider("Number of Coins to Scan", min_value=50, max_value=600, value=300, step=50)

st.sidebar.markdown("---")
st.sidebar.header("🎯 Independent Filters")

# Filter 1: EMA Position / Crossover Filter
signal_filter = st.sidebar.selectbox(
    "1️⃣ EMA Position / Crossover Filter",
    [
        "All / Any State",
        "🟢 EMA 14 Above EMA 50 (EMA 14 > EMA 50)",
        "🔴 EMA 50 Above EMA 14 (EMA 50 > EMA 14)",
        "⚡ Fresh Bullish Crossover Just Now",
        "⚡ Fresh Bearish Crossover Just Now"
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

# Fetch KuCoin USDT Pairs & 24h Ticker Data Dynamically
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

# Function to calculate EMA and check conditions
def check_ema_status(exchange, symbol, tf, ticker):
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
        
        # Use 24h Change % from ticker
        if ticker and 'percentage' in ticker and ticker['percentage'] is not None:
            price_change_pct = ticker['percentage']
        else:
            price_change_pct = ((curr_price - df['close'].iloc[-2]) / df['close'].iloc[-2]) * 100
            
        volume_24h = ticker.get('quoteVolume', df['volume'].iloc[-1] * curr_price) if ticker else df['volume'].iloc[-1] * curr_price
        ema_gap = ((curr_ema14 - curr_ema50) / curr_ema50) * 100
        
        is_fresh_bull_cross = (prev_ema14 <= prev_ema50) and (curr_ema14 > curr_ema50)
        is_fresh_bear_cross = (prev_ema14 >= prev_ema50) and (curr_ema14 < curr_ema50)
        
        if is_fresh_bull_cross:
            status_text = "⚡ FRESH BULLISH CROSS"
        elif is_fresh_bear_cross:
            status_text = "⚡ FRESH BEARISH CROSS"
        elif curr_ema14 > curr_ema50:
            status_text = "🟢 EMA 14 > EMA 50 (Bullish Zone)"
        else:
            status_text = "🔴 EMA 50 > EMA 14 (Bearish Zone)"
            
        return {
            "Symbol": symbol,
            "Price": curr_price,
            "EMA 14": curr_ema14,
            "EMA 50": curr_ema50,
            "Gap %": round(ema_gap, 2),
            "24h Change %": round(price_change_pct, 2),
            "Volume ($)": f"${volume_24h:,.0f}" if volume_24h else "$0",
            "Status": status_text,
            "EMA14_Above": curr_ema14 > curr_ema50,
            "Fresh_Bull": is_fresh_bull_cross,
            "Fresh_Bear": is_fresh_bear_cross
        }
    except Exception:
        return None

# Render Advance Cards Layout
def render_coin_cards(df_list):
    if df_list.empty:
        st.info("No coin match di selected filters.")
        return
        
    cols_per_row = 3
    cols = st.columns(cols_per_row)
    
    for idx, row in df_list.reset_index(drop=True).iterrows():
        col = cols[idx % cols_per_row]
        with col:
            if row['EMA14_Above']:
                border_color = "#10B981"
                bg_style = "rgba(16, 185, 129, 0.1)"
            else:
                border_color = "#EF4444"
                bg_style = "rgba(239, 68, 68, 0.1)"
                
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
                            <span style="color:{'#10B981' if row['24h Change %'] >= 0 else '#EF4444'}"><b>Chg:</b> {row['24h Change %']}%</span>
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
    symbols, tickers = get_kucoin_usdt_pairs(limit_coins)
    
    if not symbols:
        st.warning("No KuCoin pairs found.")
    else:
        st.info(f"Scanning top {len(symbols)} USDT pairs on KuCoin...")
        progress_bar = st.progress(0)
        results = []
        
        for i, sym in enumerate(symbols):
            sym_ticker = tickers.get(sym, {})
            res = check_ema_status(exchange, sym, timeframe, sym_ticker)
            if res:
                results.append(res)
            progress_bar.progress((i + 1) / len(symbols))
            
        df_results = pd.DataFrame(results)
        
        if not df_results.empty:
            filtered_df = df_results.copy()
            
            # Apply Filter 1: EMA Position / Cross Filter
            if signal_filter == "🟢 EMA 14 Above EMA 50 (EMA 14 > EMA 50)":
                filtered_df = filtered_df[filtered_df['EMA14_Above'] == True]
            elif signal_filter == "🔴 EMA 50 Above EMA 14 (EMA 50 > EMA 14)":
                filtered_df = filtered_df[filtered_df['EMA14_Above'] == False]
            elif signal_filter == "⚡ Fresh Bullish Crossover Just Now":
                filtered_df = filtered_df[filtered_df['Fresh_Bull'] == True]
            elif signal_filter == "⚡ Fresh Bearish Crossover Just Now":
                filtered_df = filtered_df[filtered_df['Fresh_Bear'] == True]
                
            # Apply Filter 2: Gainer / Loser Filter
            if performance_filter == "🚀 Top Gainers Only (% Change High to Low)":
                filtered_df = filtered_df[filtered_df['24h Change %'] > 0]
                filtered_df = filtered_df.sort_values(by='24h Change %', ascending=False)
            elif performance_filter == "📉 Top Losers Only (% Change Low to High)":
                filtered_df = filtered_df[filtered_df['24h Change %'] < 0]
                filtered_df = filtered_df.sort_values(by='24h Change %', ascending=True)
            else:
                filtered_df = filtered_df.sort_values(by='Gap %', ascending=True)

            # Summary Metrics Bar
            bullish_zone_count = len(df_results[df_results['EMA14_Above'] == True])
            bearish_zone_count = len(df_results[df_results['EMA14_Above'] == False])
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Scanned", len(df_results))
            m2.metric("🟢 EMA 14 > EMA 50", bullish_zone_count)
            m3.metric("🔴 EMA 50 > EMA 14", bearish_zone_count)
            m4.metric("Matching Filter Results", len(filtered_df))
            
            st.write("---")
            
            # Display Options Tabs
            tab1, tab2 = st.tabs(["🎴 Advance Cards View", "📋 Complete Table View"])
            
            with tab1:
                st.subheader(f"Results ({len(filtered_df)} Coins Found)")
                render_coin_cards(filtered_df)
                
            with tab2:
                st.subheader("📋 Table View")
                st.dataframe(filtered_df, use_container_width=True)
