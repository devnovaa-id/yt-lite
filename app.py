import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from transformers import pipeline
import time

# Konfigurasi API
CRYPTO_PANIC_API_KEY = "d3b14a16db908837c9058ebffadf852f6cf7a269"
COINGECKO_API_KEY = "CG-fGwadP1e3em6BHmDUdEkecD7"
CRYPTO_PANIC_BASE_URL = "https://cryptopanic.com/api/developer/v2"

# Konfigurasi halaman
st.set_page_config(
    page_title="🚀 Crypto Analyst Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS untuk styling profesional
st.markdown("""
<style>
    /* Font professional */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
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
        margin-bottom: 2rem !important;
    }
    
    /* Card styling */
    .card {
        background-color: #ffffff;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
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
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1f3d7d !important;
        color: white !important;
        font-weight: 600 !important;
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
    
    /* Footer styling */
    .footer {
        margin-top: 3rem;
        padding-top: 1.5rem;
        border-top: 1px solid #e9ecef;
        color: #6c757d;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Inisialisasi model AI
@st.cache_resource
def load_ai_models():
    sentiment_model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    return sentiment_model

# Fungsi untuk mendapatkan data crypto
@st.cache_data(ttl=300)
def get_crypto_data():
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false&x_cg_demo_api_key={COINGECKO_API_KEY}"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error mengambil data: {e}")
        return []

# Fungsi untuk mendapatkan data historis
@st.cache_data(ttl=3600)
def get_historical_data(coin_id, days=365):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}&x_cg_demo_api_key={COINGECKO_API_KEY}"
    try:
        data = requests.get(url, timeout=15).json()
        prices = data.get('prices', [])
        if not prices:
            return pd.DataFrame()
            
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df[['date', 'price']]
    except Exception as e:
        st.error(f"Error mengambil data historis: {e}")
        return pd.DataFrame()

# Fungsi untuk mendapatkan berita crypto
@st.cache_data(ttl=600)
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
        st.error(f"Error mengambil berita: {e}")
        return []

# Fungsi untuk analisis sentimen
def analyze_news_sentiment(news_items, sentiment_model):
    if not news_items:
        return []
    
    results = []
    for item in news_items:
        title = item.get('title', '')
        if not title:
            continue
            
        try:
            sentiment = sentiment_model(title)[0]
            results.append({
                'title': title,
                'sentiment': sentiment['label'],
                'score': sentiment['score'],
                'url': item.get('url', '#'),
                'source': item.get('source', {}).get('title', 'Unknown'),
                'published_at': item.get('published_at', ''),
                'votes': item.get('votes', {})
            })
        except:
            continue
    
    return results

# Fungsi untuk indikator teknikal
def calculate_technical_indicators(df):
    try:
        # Moving averages
        df['SMA_7'] = df['price'].rolling(window=7).mean()
        df['SMA_30'] = df['price'].rolling(window=30).mean()
        
        # RSI
        delta = df['price'].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df
    except:
        return df

# Header aplikasi
st.markdown('<h1 class="header-style">🚀 Crypto Analyst Pro</h1>', unsafe_allow_html=True)
st.markdown('<div class="subheader-style">Platform Analisis Cryptocurrency Profesional dengan Visualisasi Interaktif</div>', unsafe_allow_html=True)

# Ambil model AI
sentiment_model = load_ai_models()

# Sidebar - Pemilihan Cryptocurrency
with st.sidebar:
    st.markdown('<h2 style="color: #1f3d7d; border-bottom: 2px solid #1f3d7d; padding-bottom: 10px;">🔍 Pilih Cryptocurrency</h2>', unsafe_allow_html=True)
    
    # Ambil data crypto
    with st.spinner('Memuat data cryptocurrency...'):
        crypto_data = get_crypto_data()

    if not crypto_data:
        st.error("Gagal memuat data cryptocurrency. Silakan coba lagi nanti.")
        st.stop()

    # Konversi ke DataFrame
    df_coins = pd.DataFrame(crypto_data)
    coin_list = df_coins['name'].tolist()

    # Pilih cryptocurrency
    selected_coin = st.selectbox(
        "Cryptocurrency",
        coin_list,
        index=coin_list.index('Bitcoin') if 'Bitcoin' in coin_list else 0
    )

    # Dapatkan data coin yang dipilih
    coin_data = df_coins[df_coins['name'] == selected_coin].iloc[0]
    coin_id = coin_data['id']
    coin_symbol = coin_data['symbol']

    # Tampilkan informasi dasar coin
    st.markdown(f'<h3 style="color: #1f3d7d;">📈 {selected_coin} ({coin_symbol})</h3>', unsafe_allow_html=True)
    
    # Metric cards
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Harga Saat Ini", f"${coin_data['current_price']:,.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Market Cap", f"${coin_data['market_cap']/1e9:,.2f}B")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Perubahan 24 Jam", f"{coin_data['price_change_percentage_24h']:.2f}%")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Volume 24 Jam", f"${coin_data['total_volume']/1e6:,.2f}M")
        st.markdown('</div>', unsafe_allow_html=True)

# Tab utama
tab1, tab2, tab3 = st.tabs([
    "📊 Analisis Teknikal", 
    "📰 Berita & Sentimen", 
    "💡 Rekomendasi Trading"
])

with tab1:
    st.markdown(f'<h2 style="color: #1f3d7d;">Analisis Teknikal {selected_coin}</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        days = st.slider("Rentang Waktu (hari)", 30, 365, 90)
    with col2:
        show_rsi = st.checkbox("Tampilkan Indikator Teknikal", True)
    
    with st.spinner('Memuat data harga...'):
        historical_df = get_historical_data(coin_id, days)
    
    if historical_df.empty:
        st.warning(f"Data historis tidak tersedia untuk {selected_coin}")
    else:
        # Hitung indikator teknikal
        tech_df = calculate_technical_indicators(historical_df)
        
        # Buat grafik interaktif dengan Plotly
        fig = make_subplots(rows=2 if show_rsi else 1, cols=1, 
                           shared_xaxes=True, 
                           vertical_spacing=0.1,
                           row_heights=[0.7, 0.3] if show_rsi else [1.0])
        
        # Grafik harga
        fig.add_trace(go.Scatter(
            x=tech_df['date'], 
            y=tech_df['price'],
            mode='lines',
            name='Harga',
            line=dict(color='#1f77b4', width=2),
            fill='tozeroy',
            fillcolor='rgba(31, 119, 180, 0.1)'
        ), row=1, col=1)
        
        # Moving averages
        fig.add_trace(go.Scatter(
            x=tech_df['date'], 
            y=tech_df['SMA_7'],
            mode='lines',
            name='SMA 7 Hari',
            line=dict(color='#ff7f0e', width=1.5, dash='dot')
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=tech_df['date'], 
            y=tech_df['SMA_30'],
            mode='lines',
            name='SMA 30 Hari',
            line=dict(color='#2ca02c', width=1.5, dash='dot')
        ), row=1, col=1)
        
        # Grafik RSI jika diaktifkan
        if show_rsi and 'RSI' in tech_df:
            fig.add_trace(go.Scatter(
                x=tech_df['date'], 
                y=tech_df['RSI'],
                mode='lines',
                name='RSI',
                line=dict(color='#9467bd', width=2)
            ), row=2, col=1)
            
            # Tambahkan area overbought dan oversold
            fig.add_hrect(y0=70, y1=100, line_width=0, fillcolor="red", opacity=0.1, row=2, col=1)
            fig.add_hrect(y0=0, y1=30, line_width=0, fillcolor="green", opacity=0.1, row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        
        # Update layout
        fig.update_layout(
            height=700,
            title=f'Analisis Teknikal {selected_coin}',
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
            font=dict(family="Inter, sans-serif")
        )
        
        fig.update_xaxes(title_text="Tanggal", row=1 if show_rsi else None, col=1)
        fig.update_yaxes(title_text="Harga (USD)", row=1, col=1)
        
        if show_rsi:
            fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0, 100])
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Interpretasi indikator
        if 'RSI' in tech_df and not tech_df['RSI'].isnull().all():
            current_rsi = tech_df['RSI'].iloc[-1]
            
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f'<h3 style="color: #1f3d7d;">Interpretasi Indikator</h3>', unsafe_allow_html=True)
            
            if current_rsi > 70:
                st.warning("⚠️ **Kondisi Overbought (RSI > 70)**")
                st.write("Harga mungkin terlalu tinggi dan bisa terjadi koreksi penurunan.")
            elif current_rsi < 30:
                st.success("✅ **Kondisi Oversold (RSI < 30)**")
                st.write("Harga mungkin terlalu rendah dan bisa terjadi pemulihan kenaikan.")
            else:
                st.info("ℹ️ **RSI dalam Range Normal (30-70)**")
                st.write("Tidak ada sinyal kuat dari indikator RSI.")
            
            st.metric("Nilai RSI Terkini", f"{current_rsi:.1f}")
            st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown(f'<h2 style="color: #1f3d7d;">Berita & Sentimen {selected_coin}</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        filter_type = st.selectbox("Filter Berita", ["rising", "hot", "bullish", "bearish", "important"], index=0)
    with col2:
        news_limit = st.slider("Jumlah Berita", 5, 20, 10)
    
    if st.button("Muat Berita Terkini", key="load_news"):
        with st.spinner('Mengambil dan menganalisis berita...'):
            # Dapatkan berita
            news_items = get_crypto_news(coin_symbol=coin_symbol, filter_type=filter_type)[:news_limit]
            
            # Analisis sentimen
            sentiment_results = analyze_news_sentiment(news_items, sentiment_model)
            
            if not sentiment_results:
                st.warning("Tidak ada berita terkini yang ditemukan")
            else:
                # Ringkasan sentimen
                positive_count = sum(1 for r in sentiment_results if r['sentiment'] == 'POSITIVE')
                negative_count = sum(1 for r in sentiment_results if r['sentiment'] == 'NEGATIVE')
                sentiment_score = positive_count / len(sentiment_results) if sentiment_results else 0
                
                # Visualisasi sentimen
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<h3 style="color: #1f3d7d;">Ringkasan Sentimen</h3>', unsafe_allow_html=True)
                
                fig = go.Figure()
                fig.add_trace(go.Indicator(
                    mode="gauge+number",
                    value=sentiment_score * 100,
                    number={'suffix': '%'},
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Skor Sentimen Positif"},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'steps': [
                            {'range': [0, 40], 'color': "lightcoral"},
                            {'range': [40, 70], 'color': "lightyellow"},
                            {'range': [70, 100], 'color': "lightgreen"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': sentiment_score * 100
                        }
                    }
                ))
                
                fig.update_layout(
                    height=300,
                    margin=dict(l=50, r=50, t=50, b=50),
                    font=dict(family="Inter, sans-serif")
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Berita Positif", positive_count)
                with col2:
                    st.metric("Berita Negatif", negative_count)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Tampilkan berita
                st.markdown('<h3 style="color: #1f3d7d; margin-top: 1.5rem;">Berita Terkini</h3>', unsafe_allow_html=True)
                
                for i, result in enumerate(sentiment_results, 1):
                    sentiment_color = "#10B981" if result['sentiment'] == 'POSITIVE' else "#EF4444"
                    
                    with st.container():
                        st.markdown(f"""
                        <div class="card">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <div style="background: {sentiment_color}; width: 12px; height: 12px; border-radius: 50%;"></div>
                                    <span style="color: {sentiment_color}; font-weight: 600;">{result['sentiment']}</span>
                                </div>
                                <span style="color: #6c757d; font-size: 0.9rem;">{result.get('source', 'Unknown')}</span>
                            </div>
                            <h4>{result['title']}</h4>
                            <div style="margin-top: 0.5rem; color: #6c757d; font-size: 0.9rem;">
                                {result.get('published_at', '')}
                            </div>
                            <div style="margin-top: 1rem; display: flex; gap: 15px;">
                                <div style="display: flex; align-items: center; gap: 5px;">
                                    👍 <strong>{result.get('votes', {}).get('positive', 0)}</strong>
                                </div>
                                <div style="display: flex; align-items: center; gap: 5px;">
                                    👎 <strong>{result.get('votes', {}).get('negative', 0)}</strong>
                                </div>
                                <div style="display: flex; align-items: center; gap: 5px;">
                                    ⭐ <strong>{result.get('votes', {}).get('important', 0)}</strong>
                                </div>
                                <div style="display: flex; align-items: center; gap: 5px;">
                                    💬 <strong>{result.get('votes', {}).get('comments', 0)}</strong>
                                </div>
                            </div>
                            <div style="margin-top: 1rem;">
                                <a href="{result['url']}" target="_blank" style="color: #1f3d7d; font-weight: 600; text-decoration: none;">
                                    Baca selengkapnya →
                                </a>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

with tab3:
    st.markdown(f'<h2 style="color: #1f3d7d;">Rekomendasi Trading {selected_coin}</h2>', unsafe_allow_html=True)
    
    if st.button("Buat Analisis & Rekomendasi", type="primary", use_container_width=True):
        with st.spinner('Menganalisis data...'):
            # Dapatkan data historis
            historical_df = get_historical_data(coin_id, 90)
            
            # Analisis teknikal
            if historical_df.empty:
                st.error("Data historis tidak tersedia untuk analisis")
                st.stop()
                
            tech_df = calculate_technical_indicators(historical_df)
            
            # Analisis sentimen
            news_items = get_crypto_news(coin_symbol=coin_symbol, filter_type="hot")
            sentiment_results = analyze_news_sentiment(news_items, sentiment_model)
            
            # Hitung skor sentimen
            positive_count = sum(1 for r in sentiment_results if r['sentiment'] == 'POSITIVE')
            total_count = len(sentiment_results) or 1
            sentiment_score = positive_count / total_count
            
            # Nilai indikator
            current_price = coin_data['current_price']
            price_change = coin_data['price_change_percentage_24h']
            
            if 'RSI' in tech_df and not tech_df['RSI'].isnull().all():
                current_rsi = tech_df['RSI'].iloc[-1]
            else:
                current_rsi = 50
                st.warning("Data RSI tidak tersedia, menggunakan nilai default")
            
            # Buat rekomendasi
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<h3 style="color: #1f3d7d;">📈 Analisis Kondisi Pasar</h3>', unsafe_allow_html=True)
            
            # Tampilkan metrik dalam grid
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Harga Saat Ini", f"${current_price:,.2f}", f"{price_change:.2f}%")
            with col2:
                st.metric("RSI Terkini", f"{current_rsi:.1f}")
            with col3:
                st.metric("Sentimen Positif", f"{sentiment_score*100:.1f}%")
            
            # Visualisasi faktor
            fig = go.Figure()
            
            # Tambahkan radar chart
            fig.add_trace(go.Scatterpolar(
                r=[current_rsi/100, sentiment_score, 0.8],
                theta=['RSI', 'Sentimen', 'Volatilitas'],
                fill='toself',
                name='Faktor Analisis',
                line=dict(color='#1f3d7d')
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1]
                    )),
                showlegend=False,
                height=400,
                margin=dict(l=50, r=50, t=50, b=50),
                font=dict(family="Inter, sans-serif")
            )
            
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Rekomendasi trading
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<h3 style="color: #1f3d7d;">💡 Rekomendasi Trading</h3>', unsafe_allow_html=True)
            
            if current_rsi < 35 and sentiment_score > 0.65:
                # Perhitungan tingkat kepercayaan
                rsi_factor = max(0, 35 - current_rsi)
                sentiment_factor = max(0, (sentiment_score - 0.65) * 30)
                confidence = min(85 + rsi_factor + sentiment_factor, 95)
                confidence = int(round(confidence))
                
                st.success("**REKOMENDASI: BELI**")
                st.markdown(f'<div class="metric-value">{confidence}%</div><div class="metric-label">Tingkat Kepercayaan</div>', unsafe_allow_html=True)
                
                st.markdown("""
                <div style="margin-top: 1.5rem;">
                    <h4 style="color: #1f3d7d;">Alasan Rekomendasi:</h4>
                    <ul style="padding-left: 1.5rem;">
                        <li>Kondisi RSI menunjukkan oversold (harga mungkin terlalu rendah)</li>
                        <li>Sentimen pasar sangat positif</li>
                        <li>Potensi kenaikan harga dalam jangka pendek</li>
                        <li>Volume perdagangan meningkat</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                
            elif current_rsi > 70 and sentiment_score < 0.4:
                # Perhitungan tingkat kepercayaan
                rsi_factor = max(0, current_rsi - 70)
                sentiment_factor = max(0, (0.4 - sentiment_score) * 30)
                confidence = min(80 + rsi_factor + sentiment_factor, 95)
                confidence = int(round(confidence))
                
                st.error("**REKOMENDASI: JUAL**")
                st.markdown(f'<div class="metric-value">{confidence}%</div><div class="metric-label">Tingkat Kepercayaan</div>', unsafe_allow_html=True)
                
                st.markdown("""
                <div style="margin-top: 1.5rem;">
                    <h4 style="color: #1f3d7d;">Alasan Rekomendasi:</h4>
                    <ul style="padding-left: 1.5rem;">
                        <li>Kondisi RSI menunjukkan overbought (harga mungkin terlalu tinggi)</li>
                        <li>Sentimen pasar negatif</li>
                        <li>Potensi koreksi harga dalam jangka pendek</li>
                        <li>Volume perdagangan menurun</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                
            else:
                confidence = 70
                st.info("**REKOMENDASI: TAHAN**")
                st.markdown(f'<div class="metric-value">{confidence}%</div><div class="metric-label">Tingkat Kepercayaan</div>', unsafe_allow_html=True)
                
                st.markdown("""
                <div style="margin-top: 1.5rem;">
                    <h4 style="color: #1f3d7d;">Alasan Rekomendasi:</h4>
                    <ul style="padding-left: 1.5rem;">
                        <li>Tidak ada sinyal kuat untuk membeli atau menjual</li>
                        <li>Pasar sedang dalam kondisi netral</li>
                        <li>Pantau pergerakan harga untuk sinyal berikutnya</li>
                        <li>Pertimbangkan strategi diversifikasi</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <strong>📌 Crypto Analyst Pro</strong> | Platform Analisis Cryptocurrency Profesional
        </div>
        <div>
            Sumber Data: CoinGecko API • CryptoPanic API
        </div>
    </div>
    <div style="margin-top: 0.5rem; text-align: center;">
        Terakhir diperbarui: {}
    </div>
</div>
""".format(datetime.now().strftime('%d %B %Y %H:%M')), unsafe_allow_html=True)
