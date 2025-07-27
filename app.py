import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
import backend
from datetime import datetime

# Konfigurasi halaman
st.set_page_config(
    page_title="Sistem Trading Crypto Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state
if 'analysis' not in st.session_state:
    st.session_state.analysis = {}
if 'realtime_active' not in st.session_state:
    st.session_state.realtime_active = False
if 'socket_name' not in st.session_state:
    st.session_state.socket_name = None
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()
if 'bot' not in st.session_state:
    st.session_state.bot = None

# UI Sidebar
st.sidebar.header("🔒 Autentikasi Binance")
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("API Secret", type="password")
testnet = st.sidebar.checkbox("Gunakan Testnet", value=True)

if st.sidebar.button("Inisialisasi Sistem") and api_key and api_secret:
    try:
        st.session_state.bot = backend.CryptoTradingSystem(api_key, api_secret, testnet)
        st.sidebar.success("Sistem trading diinisialisasi!")
    except Exception as e:
        st.sidebar.error(f"Error: {str(e)}")

st.sidebar.header("⚙️ Parameter Trading")
symbol = st.sidebar.text_input("Simbol", "BTCUSDT").upper()
timeframe = st.sidebar.selectbox("Time Frame", ["M1", "M3", "M5", "M15", "M30", "H1", "H4"], index=2)
limit = st.sidebar.slider("Jumlah Data", 100, 1000, 500)

if st.sidebar.button("Analisis Sekarang") and st.session_state.bot:
    with st.spinner("Menganalisis data pasar..."):
        st.session_state.analysis = st.session_state.bot.get_trading_recommendation(symbol, timeframe, limit)
        st.session_state.last_update = datetime.now()

# Toggle real-time
realtime_toggle = st.sidebar.toggle("Analisis Real-time", st.session_state.realtime_active)

# Tampilan utama
st.title(f"🚀 Sistem Trading Crypto Pro: {symbol}")
st.caption(f"Terakhir diperbarui: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")

# Panel rekomendasi trading
if st.session_state.analysis and 'recommendation' in st.session_state.analysis:
    rec = st.session_state.analysis['recommendation']
    if rec == "BUY SEKARANG":
        st.success(f"## 🚀 REKOMENDASI: {rec}!")
    elif rec == "SELL SEKARANG":
        st.error(f"## 📉 REKOMENDASI: {rec}!")
    else:
        st.info(f"## ⏳ REKOMENDASI: {rec}")
else:
    st.warning("## 🔍 Silahkan konfigurasi dan mulai analisis")

# Tampilkan detail sinyal
if st.session_state.analysis and 'trend_up' in st.session_state.analysis:
    st.subheader("🔍 Detail Sinyal Trading")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Trend", 
                "🔺 Naik" if st.session_state.analysis['trend_up'] else "🔻 Turun" if st.session_state.analysis['trend_down'] else "↔ Netral",
                "EMA 9 vs EMA 21")
    col2.metric("Momentum", 
                "🟢 Beli" if st.session_state.analysis['momentum_buy'] else "🔴 Jual" if st.session_state.analysis['momentum_sell'] else "⚪ Netral",
                "RSI 7 Periode")
    col3.metric("Kekuatan Trend", 
                "💪 Kuat" if st.session_state.analysis['trend_strong'] else "🫣 Lemah",
                "ADX > 20")
    col4.metric("Volatilitas", 
                "🌊 Valid" if st.session_state.analysis['valid_volatility'] else "🍃 Tenang",
                "Range > 0.8 * ATR")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Volume", 
                "🚀 Spike" if st.session_state.analysis['volume_spike'] else "📉 Normal",
                "Volume > 1.5x Rata-rata")
    col2.metric("Pola Candle", 
                "🟢 Bullish" if st.session_state.analysis['bull_candle'] else "🔴 Bearish" if st.session_state.analysis['bear_candle'] else "⚪ Netral",
                "Konfirmasi Candlestick")
    col3.metric("Sinyal MACD", 
                "🟢 Beli" if st.session_state.analysis['macd_buy'] else "🔴 Jual" if st.session_state.analysis['macd_sell'] else "⚪ Netral",
                "Wavelet-MACD Pro")
    col4.metric("Sinyal Grid", 
                "🟢 Beli" if st.session_state.analysis['grid_buy'] else "🔴 Jual" if st.session_state.analysis['grid_sell'] else "⚪ Netral",
                "Dynamic Grid Trading")

# Manajemen Risiko
if st.session_state.analysis and 'last_close' in st.session_state.analysis:
    st.subheader("🛡️ Manajemen Risiko")
    
    if st.session_state.analysis['recommendation'] == "BUY SEKARANG":
        entry_price = st.session_state.analysis['last_close']
        stop_loss = st.session_state.analysis['stop_loss_buy']
        take_profit = st.session_state.analysis['take_profit_buy']
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Harga Entry", f"${entry_price:.4f}")
        col2.metric("Stop Loss", f"${stop_loss:.4f}", f"{(stop_loss-entry_price)/entry_price*100:.2f}%")
        col3.metric("Take Profit", f"${take_profit:.4f}", f"{(take_profit-entry_price)/entry_price*100:.2f}%")
        
        st.info(f"🔺 Rasio Risk:Reward = 1:{abs((take_profit-entry_price)/(entry_price-stop_loss)):.1f}")
        
    elif st.session_state.analysis['recommendation'] == "SELL SEKARANG":
        entry_price = st.session_state.analysis['last_close']
        stop_loss = st.session_state.analysis['stop_loss_sell']
        take_profit = st.session_state.analysis['take_profit_sell']
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Harga Entry", f"${entry_price:.4f}")
        col2.metric("Stop Loss", f"${stop_loss:.4f}", f"{(stop_loss-entry_price)/entry_price*100:.2f}%")
        col3.metric("Take Profit", f"${take_profit:.4f}", f"{(take_profit-entry_price)/entry_price*100:.2f}%")
        
        st.info(f"🔻 Rasio Risk:Reward = 1:{abs((entry_price-take_profit)/(stop_loss-entry_price)):.1f}")

# Grafik analisis
if st.session_state.analysis and 'last_close' in st.session_state.analysis:
    # Buat grafik candlestick interaktif
    fig = go.Figure()
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=st.session_state.df['timestamp'],
        open=st.session_state.df['open'],
        high=st.session_state.df['high'],
        low=st.session_state.df['low'],
        close=st.session_state.df['close'],
        name='Harga'
    ))
    
    # EMA
    fig.add_trace(go.Scatter(
        x=st.session_state.df['timestamp'],
        y=st.session_state.df['EMA_FAST'],
        mode='lines',
        name='EMA 9',
        line=dict(color='blue', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=st.session_state.df['timestamp'],
        y=st.session_state.df['EMA_SLOW'],
        mode='lines',
        name='EMA 21',
        line=dict(color='orange', width=2)
    ))
    
    # Dynamic Grid
    fig.add_trace(go.Scatter(
        x=st.session_state.df['timestamp'],
        y=st.session_state.df['GRID_UP'],
        mode='lines',
        name='Resistance',
        line=dict(color='red', dash='dash', width=1)
    ))
    
    fig.add_trace(go.Scatter(
        x=st.session_state.df['timestamp'],
        y=st.session_state.df['CENTER'],
        mode='lines',
        name='Midline',
        line=dict(color='gray', dash='dash', width=1)
    ))
    
    fig.add_trace(go.Scatter(
        x=st.session_state.df['timestamp'],
        y=st.session_state.df['GRID_LOW'],
        mode='lines',
        name='Support',
        line=dict(color='green', dash='dash', width=1),
        fill='tonexty'
    ))
    
    # Rekomendasi trading
    last_rec = st.session_state.analysis['recommendation']
    last_close = st.session_state.analysis['last_close']
    if last_rec != "TUNGGU / NO TRADE":
        fig.add_annotation(
            x=st.session_state.df['timestamp'].iloc[-1],
            y=last_close,
            text=last_rec,
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=-40 if "BELI" in last_rec else 40,
            bgcolor="green" if "BELI" in last_rec else "red",
            font=dict(color="white", size=14)
        )
    
    fig.update_layout(
        title=f"{symbol} - Analisis Harga",
        xaxis_rangeslider_visible=False,
        height=600,
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Grafik indikator
    fig2 = go.Figure()
    
    # RSI
    fig2.add_trace(go.Scatter(
        x=st.session_state.df['timestamp'],
        y=st.session_state.df['RSI'],
        mode='lines',
        name='RSI',
        line=dict(color='cyan', width=2),
        yaxis='y1'
    ))
    fig2.add_hline(y=30, line_dash="dash", line_color="green")
    fig2.add_hline(y=70, line_dash="dash", line_color="red")
    
    # MACD
    fig2.add_trace(go.Bar(
        x=st.session_state.df['timestamp'],
        y=st.session_state.df['MACD'],
        name='MACD Histogram',
        marker_color=np.where(st.session_state.df['MACD'] > 0, 'green', 'red'),
        yaxis='y2'
    ))
    
    fig2.add_trace(go.Scatter(
        x=st.session_state.df['timestamp'],
        y=st.session_state.df['DIF'],
        mode='lines',
        name='DIF',
        line=dict(color='yellow', width=2),
        yaxis='y2'
    ))
    
    fig2.add_trace(go.Scatter(
        x=st.session_state.df['timestamp'],
        y=st.session_state.df['DEA'],
        mode='lines',
        name='DEA',
        line=dict(color='purple', width=2),
        yaxis='y2'
    ))
    
    fig2.update_layout(
        title="Indikator Momentum",
        height=400,
        template="plotly_dark",
        yaxis=dict(title="RSI", domain=[0.6, 1.0]),
        yaxis2=dict(title="MACD", domain=[0.0, 0.4])
    )
    st.plotly_chart(fig2, use_container_width=True)

# Real-time handling
def handle_realtime_message(msg):
    try:
        if msg['e'] == 'kline' and msg['k']['x']:  # Hanya saat candle tertutup
            st.session_state.last_update = datetime.now()
            if st.session_state.bot:
                st.session_state.analysis = st.session_state.bot.get_trading_recommendation(symbol, timeframe, limit)
                st.rerun()
    except Exception as e:
        st.error(f"Error in real-time handler: {e}")

# Aktifkan/matikan real-time
if realtime_toggle and st.session_state.bot:
    if not st.session_state.realtime_active:
        st.session_state.socket_name = st.session_state.bot.start_realtime(symbol, timeframe, handle_realtime_message)
        st.session_state.realtime_active = True
        st.sidebar.success("Analisis real-time diaktifkan!")
else:
    if st.session_state.realtime_active and st.session_state.bot:
        st.session_state.bot.stop_realtime(st.session_state.socket_name)
        st.session_state.realtime_active = False
        st.sidebar.info("Analisis real-time dimatikan")

# Auto-refresh untuk real-time
if st.session_state.realtime_active:
    time.sleep(1)  # Refresh setiap 1 detik
    st.rerun()

# Footer
st.markdown("---")
st.caption("© 2024 Sistem Trading Crypto Pro | Binance API | Real-time Analysis")

# Instruksi penggunaan
st.sidebar.markdown("""
## 📖 Panduan Penggunaan
1. Masukkan API Key Binance
2. Pilih simbol trading (contoh: BTCUSDT)
3. Pilih timeframe (M1, M5, H1, dll)
4. Klik "Analisis Sekarang" untuk analisis manual
5. Aktifkan "Analisis Real-time" untuk update otomatis
6. Ikuti rekomendasi trading dengan manajemen risiko

## ⚠️ Manajemen Risiko
- Gunakan stop loss dan take profit
- Risiko maksimal 1% per trade
- Verifikasi sinyal dengan timeframe lebih tinggi
- Gunakan testnet sebelum trading nyata
""")
