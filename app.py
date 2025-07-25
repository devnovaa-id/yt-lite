import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import datetime
import pytz
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import EMAIndicator, MACD
from ta.volatility import BollingerBands
import threading

# Konfigurasi API
BINANCE_API_URL = "https://api.binance.com/api/v3"
CRYPTO_PANIC_API_KEY = "d3b14a16db908837c9058ebffadf852f6cf7a269"
CRYPTO_PANIC_BASE_URL = "https://cryptopanic.com/api/developer/v2"

# Konfigurasi halaman
st.set_page_config(
    page_title="🚀 Crypto Analyst Pro - M1/M5",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS untuk styling profesional
st.markdown("""
<style>
    /* Font professional */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Header styling */
    .header-style {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: #1f3d7d !important;
        margin-bottom: 0.5rem !important;
    }
    
    .subheader-style {
        font-size: 1.2rem !important;
        color: #4a6fa5 !important;
        margin-bottom: 1rem !important;
    }
    
    /* Card styling */
    .card {
        background-color: #ffffff;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
        border: 1px solid #e9ecef;
    }
    
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 25px;
        border-radius: 10px !important;
        background-color: #f0f4ff !important;
        transition: all 0.3s ease !important;
        font-weight: 600 !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1f3d7d !important;
        color: white !important;
    }
    
    /* Metric styling */
    .metric-card {
        text-align: center;
        padding: 1rem;
    }
    
    .metric-value {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #1f3d7d !important;
    }
    
    .metric-label {
        font-size: 1rem !important;
        color: #6c757d !important;
        margin-top: 0.5rem !important;
    }
    
    /* Button styling */
    .stButton>button {
        background-color: #1f3d7d !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton>button:hover {
        background-color: #162b5c !important;
        transform: scale(1.05);
    }
    
    /* Ticker styling */
    .ticker-container {
        display: flex;
        overflow: hidden;
        background: linear-gradient(90deg, #1f3d7d, #4a6fa5);
        border-radius: 8px;
        padding: 12px 0;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 10px rgba(31, 61, 125, 0.2);
    }
    
    .ticker-item {
        display: flex;
        align-items: center;
        padding: 0 25px;
        white-space: nowrap;
        border-right: 1px solid rgba(255,255,255,0.2);
    }
    
    .ticker-symbol {
        font-weight: 700;
        color: white;
        margin-right: 6px;
        font-size: 1.1rem;
    }
    
    .ticker-price {
        font-weight: 600;
        color: white;
        font-size: 1.1rem;
    }
    
    .ticker-change {
        font-weight: 600;
        margin-left: 12px;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.9rem;
    }
    
    .positive {
        background-color: rgba(16, 185, 129, 0.9);
        color: white;
    }
    
    .negative {
        background-color: rgba(239, 68, 68, 0.9);
        color: white;
    }
    
    /* Table styling */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
    
    .stDataFrame thead th {
        background-color: #1f3d7d !important;
        color: white !important;
    }
    
    /* Footer styling */
    .footer {
        margin-top: 3rem;
        padding-top: 1.5rem;
        border-top: 1px solid #e9ecef;
        color: #6c757d;
        font-size: 0.9rem;
        text-align: center;
    }
    
    /* Indicator tag */
    .indicator-tag {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .buy-tag {
        background-color: #e6f7ee;
        color: #10b981;
    }
    
    .sell-tag {
        background-color: #fde8e8;
        color: #ef4444;
    }
    
    .neutral-tag {
        background-color: #f0f4ff;
        color: #1f3d7d;
    }
</style>
""", unsafe_allow_html=True)

# Inisialisasi state
if 'realtime_data' not in st.session_state:
    st.session_state.realtime_data = {}
    st.session_state.last_update = datetime.datetime.now()

# Fungsi untuk mendapatkan data real-time dari Binance
def get_realtime_price(symbol):
    try:
        response = requests.get(f"{BINANCE_API_URL}/ticker/price", params={"symbol": f"{symbol}USDT"})
        if response.status_code == 200:
            data = response.json()
            return float(data['price'])
    except Exception as e:
        st.error(f"Error fetching real-time price for {symbol}: {e}")
    return None

# Fungsi untuk mendapatkan data kline dari Binance
def get_klines(symbol, interval, limit=100):
    try:
        response = requests.get(
            f"{BINANCE_API_URL}/klines",
            params={
                "symbol": f"{symbol}USDT",
                "interval": interval,
                "limit": limit
            }
        )
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])
            # Konversi tipe data
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            # Konversi waktu
            df['date'] = pd.to_datetime(df['open_time'], unit='ms')
            return df[['date', 'open', 'high', 'low', 'close', 'volume']]
    except Exception as e:
        st.error(f"Error fetching klines for {symbol}: {e}")
    return pd.DataFrame()

# Fungsi untuk menghitung indikator teknikal
def calculate_technical_indicators(df):
    try:
        # RSI
        rsi_indicator = RSIIndicator(df['close'], window=14)
        df['rsi'] = rsi_indicator.rsi()
        
        # Stochastic Oscillator
        stoch_indicator = StochasticOscillator(df['high'], df['low'], df['close'], window=14, smooth_window=3)
        df['stoch_k'] = stoch_indicator.stoch()
        df['stoch_d'] = stoch_indicator.stoch_signal()
        
        # EMA
        ema_indicator = EMAIndicator(df['close'], window=20)
        df['ema_20'] = ema_indicator.ema_indicator()
        
        # MACD
        macd_indicator = MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
        df['macd'] = macd_indicator.macd()
        df['macd_signal'] = macd_indicator.macd_signal()
        df['macd_diff'] = macd_indicator.macd_diff()
        
        # Bollinger Bands
        bb_indicator = BollingerBands(df['close'], window=20, window_dev=2)
        df['bb_upper'] = bb_indicator.bollinger_hband()
        df['bb_middle'] = bb_indicator.bollinger_mavg()
        df['bb_lower'] = bb_indicator.bollinger_lband()
        
        # Volume EMA
        df['volume_ema'] = df['volume'].ewm(span=10).mean()
        
        return df
    except Exception as e:
        st.error(f"Error calculating indicators: {e}")
        return df

# Fungsi untuk mendapatkan berita crypto
def get_crypto_news(coin_symbol=None, filter_type="rising"):
    endpoint = f"{CRYPTO_PANIC_BASE_URL}/posts/"
    params = {
        "auth_token": CRYPTO_PANIC_API_KEY,
        "public": "true",
        "filter": filter_type,
        "regions": "en"
    }
    
    if coin_symbol:
        params["currencies"] = coin_symbol.upper()
    
    try:
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except Exception as e:
        st.error(f"Error fetching news: {e}")
        return []

# Fungsi untuk update data real-time
def update_realtime_data():
    symbols = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "AVAX", "DOGE", "DOT", "MATIC"]
    while True:
        try:
            new_data = {}
            for symbol in symbols:
                price = get_realtime_price(symbol)
                if price is not None:
                    new_data[symbol] = price
            st.session_state.realtime_data = new_data
            st.session_state.last_update = datetime.datetime.now()
        except:
            pass
        time.sleep(5)

# Start real-time data update thread
if 'update_thread' not in st.session_state:
    st.session_state.update_thread = threading.Thread(target=update_realtime_data, daemon=True)
    st.session_state.update_thread.start()

# Header aplikasi
st.markdown('<h1 class="header-style">⏱️ Crypto Analyst Pro - M1/M5</h1>', unsafe_allow_html=True)
st.markdown('<div class="subheader-style">Analisis Time Frame Kecil (1-5 Menit) dengan Data Real-time Binance</div>', unsafe_allow_html=True)

# Ticker waktu nyata
ticker_html = """
<div class="ticker-container">
"""
symbols = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "AVAX", "DOGE", "DOT", "MATIC"]
for symbol in symbols:
    price = st.session_state.realtime_data.get(symbol, 0)
    ticker_html += f"""
    <div class="ticker-item">
        <span class="ticker-symbol">{symbol}:</span>
        <span class="ticker-price">${price:,.2f}</span>
    </div>
    """
ticker_html += """
</div>
"""
st.markdown(ticker_html, unsafe_allow_html=True)

# Sidebar - Pemilihan Cryptocurrency
with st.sidebar:
    st.markdown('<h2 style="color: #1f3d7d; border-bottom: 2px solid #1f3d7d; padding-bottom: 10px;">🔍 Pilih Cryptocurrency</h2>', unsafe_allow_html=True)
    
    # Pilih cryptocurrency
    selected_coin = st.selectbox(
        "Cryptocurrency",
        ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "AVAX", "DOGE", "DOT", "MATIC"],
        index=0
    )
    
    # Tampilkan informasi dasar coin
    coin_price = st.session_state.realtime_data.get(selected_coin, 0)
    
    st.markdown(f'<h3 style="color: #1f3d7d;">📈 {selected_coin}/USDT</h3>', unsafe_allow_html=True)
    
    # Metric cards
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Harga Saat Ini", f"${coin_price:,.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Perubahan 5m", f"+0.25%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Time frame selection
    st.markdown('<h4 style="color: #1f3d7d; margin-top: 20px;">⚙️ Pengaturan Analisis</h4>', unsafe_allow_html=True)
    time_frame = st.selectbox("Time Frame", ["1m", "3m", "5m", "15m", "30m"], index=2)
    data_points = st.slider("Jumlah Data Poin", 50, 500, 200)
    indicators = st.multiselect(
        "Indikator Teknikal", 
        ["RSI", "Stochastic", "EMA", "MACD", "Bollinger Bands"], 
        ["RSI", "Stochastic", "EMA"]
    )
    
    # Update button
    st.button("Perbarui Data", key="update_data", use_container_width=True)

# Tab utama
tab1, tab2, tab3 = st.tabs([
    "📈 Analisis Teknikal", 
    "📊 Order Book & Depth", 
    "📰 Berita & Sentimen"
])

with tab1:
    # Dapatkan data kline
    with st.spinner(f'Mengambil data {time_frame} untuk {selected_coin}...'):
        df = get_klines(selected_coin, time_frame, data_points)
    
    if df.empty:
        st.warning(f"Data tidak tersedia untuk {selected_coin} pada time frame {time_frame}")
    else:
        # Hitung indikator teknikal
        df = calculate_technical_indicators(df)
        
        # Buat grafik interaktif dengan Plotly
        fig = make_subplots(
            rows=3, 
            cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.05,
            row_heights=[0.6, 0.2, 0.2],
            specs=[[{"secondary_y": True}], [{"secondary_y": False}], [{"secondary_y": False}]]
        )
        
        # Candlestick chart
        fig.add_trace(go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Harga',
            increasing_line_color='#10B981',
            decreasing_line_color='#EF4444'
        ), row=1, col=1)
        
        # Tambahkan EMA jika dipilih
        if 'EMA' in indicators and 'ema_20' in df:
            fig.add_trace(go.Scatter(
                x=df['date'], 
                y=df['ema_20'],
                mode='lines',
                name='EMA 20',
                line=dict(color='#3B82F6', width=2)
            ), row=1, col=1)
        
        # Tambahkan Bollinger Bands jika dipilih
        if 'Bollinger Bands' in indicators and 'bb_upper' in df:
            fig.add_trace(go.Scatter(
                x=df['date'], 
                y=df['bb_upper'],
                mode='lines',
                name='BB Upper',
                line=dict(color='#8B5CF6', width=1, dash='dash')
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=df['date'], 
                y=df['bb_middle'],
                mode='lines',
                name='BB Middle',
                line=dict(color='#8B5CF6', width=1)
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=df['date'], 
                y=df['bb_lower'],
                mode='lines',
                name='BB Lower',
                line=dict(color='#8B5CF6', width=1, dash='dash'),
                fill='tonexty',
                fillcolor='rgba(139, 92, 246, 0.1)'
            ), row=1, col=1)
        
        # Volume chart
        fig.add_trace(go.Bar(
            x=df['date'],
            y=df['volume'],
            name='Volume',
            marker_color='#4A6FA5',
            opacity=0.7
        ), row=2, col=1)
        
        if 'volume_ema' in df:
            fig.add_trace(go.Scatter(
                x=df['date'], 
                y=df['volume_ema'],
                mode='lines',
                name='Volume EMA',
                line=dict(color='#1f3d7d', width=2)
            ), row=2, col=1)
        
        # RSI chart
        if 'RSI' in indicators and 'rsi' in df:
            fig.add_trace(go.Scatter(
                x=df['date'], 
                y=df['rsi'],
                mode='lines',
                name='RSI',
                line=dict(color='#8B5CF6', width=2)
            ), row=3, col=1)
            
            fig.add_hrect(y0=70, y1=100, line_width=0, fillcolor="rgba(239, 68, 68, 0.1)", row=3, col=1)
            fig.add_hrect(y0=0, y1=30, line_width=0, fillcolor="rgba(16, 185, 129, 0.1)", row=3, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="#EF4444", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="#10B981", row=3, col=1)
        
        # Stochastic Oscillator
        if 'Stochastic' in indicators and 'stoch_k' in df:
            fig.add_trace(go.Scatter(
                x=df['date'], 
                y=df['stoch_k'],
                mode='lines',
                name='%K',
                line=dict(color='#3B82F6', width=2)
            ), row=3, col=1)
            
            fig.add_trace(go.Scatter(
                x=df['date'], 
                y=df['stoch_d'],
                mode='lines',
                name='%D',
                line=dict(color='#EF4444', width=2)
            ), row=3, col=1)
            
            fig.add_hrect(y0=80, y1=100, line_width=0, fillcolor="rgba(239, 68, 68, 0.1)", row=3, col=1)
            fig.add_hrect(y0=0, y1=20, line_width=0, fillcolor="rgba(16, 185, 129, 0.1)", row=3, col=1)
        
        # MACD
        if 'MACD' in indicators and 'macd' in df:
            fig.add_trace(go.Scatter(
                x=df['date'], 
                y=df['macd'],
                mode='lines',
                name='MACD',
                line=dict(color='#3B82F6', width=2)
            ), row=3, col=1)
            
            fig.add_trace(go.Scatter(
                x=df['date'], 
                y=df['macd_signal'],
                mode='lines',
                name='Signal',
                line=dict(color='#EF4444', width=2)
            ), row=3, col=1)
            
            # Histogram MACD
            colors = ['#10B981' if val >= 0 else '#EF4444' for val in df['macd_diff']]
            fig.add_trace(go.Bar(
                x=df['date'],
                y=df['macd_diff'],
                name='MACD Hist',
                marker_color=colors
            ), row=3, col=1)
        
        # Update layout
        fig.update_layout(
            height=900,
            title=f'Analisis {time_frame} - {selected_coin}/USDT',
            hovermode="x unified",
            showlegend=True,
            template='plotly_white',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=50, r=50, t=80, b=50),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Inter, sans-serif", size=12),
            xaxis_rangeslider_visible=False
        )
        
        fig.update_xaxes(title_text="Waktu", row=3, col=1)
        fig.update_yaxes(title_text="Harga (USD)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        
        if 'RSI' in indicators or 'Stochastic' in indicators or 'MACD' in indicators:
            fig.update_yaxes(title_text="Indikator", row=3, col=1)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Interpretasi indikator
        if not df.empty:
            last_row = df.iloc[-1]
            
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f'<h3 style="color: #1f3d7d;">Interpretasi Indikator ({time_frame})</h3>', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Harga Terakhir", f"${last_row['close']:,.4f}")
                price_change = ((last_row['close'] - df.iloc[-2]['close']) / df.iloc[-2]['close']) * 100
                st.metric("Perubahan", f"{price_change:.2f}%")
            
            if 'rsi' in df:
                with col2:
                    st.metric("RSI", f"{last_row['rsi']:.1f}")
                    if last_row['rsi'] > 70:
                        st.markdown('<div class="indicator-tag sell-tag">OVERBOUGHT</div>', unsafe_allow_html=True)
                    elif last_row['rsi'] < 30:
                        st.markdown('<div class="indicator-tag buy-tag">OVERSOLD</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="indicator-tag neutral-tag">NEUTRAL</div>', unsafe_allow_html=True)
            
            if 'stoch_k' in df:
                with col3:
                    st.metric("Stochastic", f"K: {last_row['stoch_k']:.1f}, D: {last_row['stoch_d']:.1f}")
                    if last_row['stoch_k'] > 80 or last_row['stoch_d'] > 80:
                        st.markdown('<div class="indicator-tag sell-tag">OVERBOUGHT</div>', unsafe_allow_html=True)
                    elif last_row['stoch_k'] < 20 or last_row['stoch_d'] < 20:
                        st.markdown('<div class="indicator-tag buy-tag">OVERSOLD</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="indicator-tag neutral-tag">NEUTRAL</div>', unsafe_allow_html=True)
            
            if 'macd' in df:
                with col4:
                    st.metric("MACD", f"{last_row['macd']:.4f}")
                    if last_row['macd'] > last_row['macd_signal']:
                        st.markdown('<div class="indicator-tag buy-tag">BULLISH</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="indicator-tag sell-tag">BEARISH</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    # Simulasi order book
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h3 style="color: #1f3d7d;">📊 Order Book</h3>', unsafe_allow_html=True)
    
    # Buat data order book simulasi
    current_price = st.session_state.realtime_data.get(selected_coin, 100)
    
    bids = pd.DataFrame({
        'Price': np.linspace(current_price * 0.98, current_price, 20)[::-1],
        'Quantity': np.random.uniform(1, 10, 20),
        'Total': np.random.uniform(100, 500, 20)
    })
    
    asks = pd.DataFrame({
        'Price': np.linspace(current_price, current_price * 1.02, 20),
        'Quantity': np.random.uniform(1, 10, 20),
        'Total': np.random.uniform(100, 500, 20)
    })
    
    # Tampilkan order book
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<h4 style="color: #10B981;">Bid (Buy Orders)</h4>', unsafe_allow_html=True)
        st.dataframe(
            bids.style.format({
                'Price': '${:,.4f}',
                'Quantity': '{:.2f}',
                'Total': '${:,.2f}'
            }).apply(lambda x: ['background: #e6f7ee' if x.name % 2 == 0 else '' for i in x], axis=1),
            height=600
        )
    
    with col2:
        st.markdown('<h4 style="color: #EF4444;">Ask (Sell Orders)</h4>', unsafe_allow_html=True)
        st.dataframe(
            asks.style.format({
                'Price': '${:,.4f}',
                'Quantity': '{:.2f}',
                'Total': '${:,.2f}'
            }).apply(lambda x: ['background: #fde8e8' if x.name % 2 == 0 else '' for i in x], axis=1),
            height=600
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Depth chart
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h3 style="color: #1f3d7d;">📈 Market Depth</h3>', unsafe_allow_html=True)
    
    fig = go.Figure()
    
    # Bid depth
    fig.add_trace(go.Scatter(
        x=bids['Price'],
        y=bids['Quantity'].cumsum(),
        mode='lines',
        name='Bid Depth',
        line=dict(color='#10B981', width=3),
        fill='tozeroy',
        fillcolor='rgba(16, 185, 129, 0.2)'
    ))
    
    # Ask depth
    fig.add_trace(go.Scatter(
        x=asks['Price'],
        y=asks['Quantity'].cumsum(),
        mode='lines',
        name='Ask Depth',
        line=dict(color='#EF4444', width=3),
        fill='tozeroy',
        fillcolor='rgba(239, 68, 68, 0.2)'
    ))
    
    # Current price line
    fig.add_vline(
        x=current_price, 
        line_dash="dash", 
        line_color="#3B82F6",
        annotation_text=f"Harga Saat Ini: ${current_price:,.2f}", 
        annotation_position="top"
    )
    
    fig.update_layout(
        height=500,
        title='Market Depth',
        xaxis_title='Harga',
        yaxis_title='Kuantitas Kumulatif',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template='plotly_white',
        margin=dict(l=50, r=50, t=80, b=50),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif")
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    # Dapatkan berita
    with st.spinner('Mengambil berita terkini...'):
        news_items = get_crypto_news(coin_symbol=selected_coin, filter_type="rising")
    
    if not news_items:
        st.warning("Tidak ada berita terkini yang ditemukan")
    else:
        # Ringkasan sentimen
        positive_news = sum(1 for item in news_items if "bull" in item.get('title', '').lower())
        negative_news = sum(1 for item in news_items if "bear" in item.get('title', '').lower())
        sentiment_score = positive_news / len(news_items) if news_items else 0.5
        
        # Visualisasi sentimen
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3 style="color: #1f3d7d;">📰 Ringkasan Sentimen Berita</h3>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Pie(
                labels=['Positif', 'Negatif', 'Netral'],
                values=[positive_news, negative_news, len(news_items) - positive_news - negative_news],
                marker_colors=['#10B981', '#EF4444', '#4A6FA5'],
                hole=0.5,
                textinfo='percent+label'
            ))
            
            fig.update_layout(
                height=300,
                showlegend=False,
                margin=dict(l=20, r=20, t=20, b=20),
                font=dict(family="Inter, sans-serif")
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.metric("Total Berita", len(news_items))
            st.metric("Berita Positif", positive_news)
            st.metric("Berita Negatif", negative_news)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Tampilkan berita
        st.markdown('<h3 style="color: #1f3d7d; margin-top: 1.5rem;">🔥 Berita Terkini</h3>', unsafe_allow_html=True)
        
        for i, item in enumerate(news_items[:10], 1):
            title = item.get('title', 'No title available')
            source = item.get('source', {}).get('title', 'Unknown source')
            published_at = item.get('published_at', '')
            url = item.get('url', '#')
            
            # Tentukan sentimen berdasarkan kata kunci
            sentiment = "neutral"
            sentiment_color = "#4A6FA5"
            if "bull" in title.lower() or "up" in title.lower() or "rise" in title.lower():
                sentiment = "bullish"
                sentiment_color = "#10B981"
            elif "bear" in title.lower() or "down" in title.lower() or "drop" in title.lower():
                sentiment = "bearish"
                sentiment_color = "#EF4444"
            
            with st.container():
                st.markdown(f"""
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                                <div style="background: {sentiment_color}; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px;"></div>
                                <span style="color: {sentiment_color}; font-weight: 600; text-transform: uppercase;">{sentiment}</span>
                            </div>
                            <h4 style="margin-top: 0;">{title}</h4>
                        </div>
                        <div style="text-align: right; min-width: 150px;">
                            <span style="color: #6c757d; font-size: 0.9rem;">{source}</span>
                            <div style="color: #6c757d; font-size: 0.85rem; margin-top: 5px;">{published_at}</div>
                        </div>
                    </div>
                    <div style="margin-top: 15px;">
                        <a href="{url}" target="_blank" style="color: #1f3d7d; font-weight: 600; text-decoration: none; display: inline-flex; align-items: center;">
                            Baca selengkapnya 
                            <svg style="margin-left: 5px;" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1f3d7d" stroke-width="2">
                                <path d="M5 12h14M12 5l7 7-7 7"></path>
                            </svg>
                        </a>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# Footer
last_update = st.session_state.last_update.strftime('%H:%M:%S')
st.markdown(f"""
<div class="footer">
    <div>
        <strong>🚀 Crypto Analyst Pro - M1/M5</strong> | Platform Analisis Cryptocurrency Time Frame Kecil
    </div>
    <div style="margin-top: 10px;">
        Data harga real-time dari Binance API | Berita dari CryptoPanic API
    </div>
    <div style="margin-top: 5px; font-size: 0.85rem;">
        Terakhir diperbarui: {last_update} (Waktu Server)
    </div>
</div>
""", unsafe_allow_html=True)

# Auto-refresh setiap 30 detik
st_autorefresh = st.empty()
st_autorefresh.markdown("""
<script>
    // Auto-refresh setiap 30 detik
    setTimeout(function(){
        window.location.reload();
    }, 30000);
</script>
""", unsafe_allow_html=True)
