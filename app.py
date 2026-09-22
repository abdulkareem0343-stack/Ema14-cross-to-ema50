import streamlit as st
import ccxt
import pandas as pd
from ta.trend import EMAIndicator

# Page configuration
st.set_page_config(page_title="KuCoin Advance EMA Scanner", page_icon="📈", layout="wide")

st.title("📈 KuCoin Advance EMA 14 / 50 & Gainers/Losers Scanner")
st.caption("Custom filters ke sath EMA 14/50 crossovers aur Top Gainers / Losers coins live scan karein.")

# Sidebar settings
st.sidebar.header("⚙️ Scanner Settings")
timeframe = st.sidebar.selectbox("Select Timeframe", ['5m', '15m', '1h', '4h', '1d'], index=2)
limit_coins = st.sidebar.slider("Number of Coins to Scan", min_value=50, max_value=600, value=300, step=50)

# Sidebar Filter
filter_option = st.sidebar.selectbox(
    "🎯 Select View Filter",
    [
        "All Scanned Coins",
        "🟢 Bullish Cross Only (EMA 14 > EMA 50)",
        "🔴 Bearish Cross Only (EMA 50 > EMA 14)",
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
        st.info("Koi coin is category mein nahi mila.")
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
            # Sort dataframe by Gap % in ascending order (Low to High) for table view
            df_results = df_results.sort_values(by='Gap %', ascending=True)
            
            bullish_df = df_results[df_results['Cross Type'] == 'Bullish']
            bearish_df = df_results[df_results['Cross Type'] == 'Bearish']
            gainers_df = df_results.sort_values(by='Change %', ascending=False)
            losers_df = df_results.sort_values(by='Change %', ascending=True)
            
            # Summary Metrics Bar
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Scanned", len(df_results))
            m2.metric("🟢 Bullish Crosses", len(bullish_df))
            m3.metric("🔴 Bearish Crosses", len(bearish_df))
            m4.metric("🚀 Top Gainer", f"{gainers_df.iloc[0]['Symbol']} ({gainers_df.iloc[0]['Change %']}%)" if not gainers_df.empty else "-")
            
            st.write("---")
            
            # Filter Logic Based on Sidebar Selection
            if filter_option == "🟢 Bullish Cross Only (EMA 14 > EMA 50)":
                st.subheader("🟢 Bullish Crossover Coins (EMA 14 > EMA 50)")
                render_coin_cards(bullish_df)
            elif filter_option == "🔴 Bearish Cross Only (EMA 50 > EMA 14)":
                st.subheader("🔴 Bearish Crossover Coins (EMA 50 > EMA 14)")
                render_coin_cards(bearish_df)
            elif filter_option == "🚀 Top Gainers Only (% Change High to Low)":
                st.subheader("🚀 Top Gainers Coins")
                render_coin_cards(gainers_df)
            elif filter_option == "📉 Top Losers Only (% Change Low to High)":
                st.subheader("📉 Top Losers Coins")
                render_coin_cards(losers_df)
            else:
                # Default Tabs View
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    f"🟢 Bullish ({len(bullish_df)})", 
                    f"🔴 Bearish ({len(bearish_df)})", 
                    "🚀 Top Gainers",
                    "📉 Top Losers",
                    "📋 Table View"
                ])
                
                with tab1:
                    st.subheader("🟢 Bullish Crossover Coins (EMA 14 > EMA 50)")
                    render_coin_cards(bullish_df)
                    
                with tab2:
                    st.subheader("🔴 Bearish Crossover Coins (EMA 50 > EMA 14)")
                    render_coin_cards(bearish_df)

                with tab3:
                    st.subheader("🚀 Top Gainers")
                    render_coin_cards(gainers_df)

                with tab4:
                    st.subheader("📉 Top Losers")
                    render_coin_cards(losers_df)
                    
                with tab5:
                    st.subheader("📋 Complete Table View (Sorted by Gap %: Lowest to Highest)")
                    st.dataframe(df_results, use_container_width=True)
