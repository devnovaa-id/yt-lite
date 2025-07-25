import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
from transformers import pipeline

# Konfigurasi API
CRYPTO_PANIC_API_KEY = "d3b14a16db908837c9058ebffadf852f6cf7a269"
COINGECKO_API_KEY = "CG-fGwadP1e3em6BHmDUdEkecD7"
CRYPTO_PANIC_BASE_URL = "https://cryptopanic.com/api/developer/v2"

# Konfigurasi halaman
st.set_page_config(
    page_title="📊 Crypto Analyst Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Tampilan UI
st.title("📊 Crypto Analyst Pro")
st.markdown("""
### Platform Analisis Cryptocurrency Terintegrasi
Pilih cryptocurrency untuk melihat analisis teknikal, sentimen pasar, dan rekomendasi trading
""")

# Ambil model AI
sentiment_model = load_ai_models()

# Sidebar - Pemilihan Cryptocurrency
st.sidebar.header("🔍 Pilih Cryptocurrency")

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
selected_coin = st.sidebar.selectbox(
    "Cryptocurrency",
    coin_list,
    index=coin_list.index('Bitcoin') if 'Bitcoin' in coin_list else 0
)

# Dapatkan data coin yang dipilih
coin_data = df_coins[df_coins['name'] == selected_coin].iloc[0]
coin_id = coin_data['id']
coin_symbol = coin_data['symbol']

# Tampilkan informasi dasar coin
st.sidebar.subheader(f"📈 {selected_coin} ({coin_symbol})")
st.sidebar.metric("Harga Saat Ini", f"${coin_data['current_price']:,.2f}")
st.sidebar.metric("Perubahan 24 Jam", f"{coin_data['price_change_percentage_24h']:.2f}%")
st.sidebar.metric("Market Cap", f"${coin_data['market_cap']/1e9:,.2f}B")
st.sidebar.metric("Volume 24 Jam", f"${coin_data['total_volume']/1e6:,.2f}M")

# Tab utama
tab1, tab2, tab3 = st.tabs([
    "📊 Analisis Teknikal", 
    "📰 Berita & Sentimen", 
    "💡 Rekomendasi Trading"
])

with tab1:
    st.header(f"Analisis Teknikal {selected_coin}")
    
    col1, col2 = st.columns(2)
    with col1:
        days = st.slider("Rentang Waktu (hari)", 30, 365, 90)
    with col2:
        show_rsi = st.checkbox("Tampilkan RSI", True)
    
    with st.spinner('Memuat data harga...'):
        historical_df = get_historical_data(coin_id, days)
    
    if historical_df.empty:
        st.warning(f"Data historis tidak tersedia untuk {selected_coin}")
    else:
        # Hitung indikator teknikal
        tech_df = calculate_technical_indicators(historical_df)
        
        # Grafik harga
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        # Plot harga dan moving averages
        ax1.plot(tech_df['date'], tech_df['price'], label='Harga', color='blue')
        ax1.plot(tech_df['date'], tech_df['SMA_7'], label='SMA 7 Hari', color='orange', linestyle='--')
        ax1.plot(tech_df['date'], tech_df['SMA_30'], label='SMA 30 Hari', color='green', linestyle='--')
        ax1.set_title(f'Perubahan Harga {selected_coin}', fontsize=16)
        ax1.set_xlabel('Tanggal')
        ax1.set_ylabel('Harga (USD)')
        ax1.legend(loc='upper left')
        ax1.grid(True)
        
        if show_rsi and 'RSI' in tech_df:
            # Grafik RSI
            ax2 = ax1.twinx()
            ax2.plot(tech_df['date'], tech_df['RSI'], label='RSI', color='purple', alpha=0.7)
            ax2.axhline(70, color='red', linestyle='-', alpha=0.3)
            ax2.axhline(30, color='green', linestyle='-', alpha=0.3)
            ax2.fill_between(tech_df['date'], 70, tech_df['RSI'], where=(tech_df['RSI'] > 70), color='red', alpha=0.1)
            ax2.fill_between(tech_df['date'], 30, tech_df['RSI'], where=(tech_df['RSI'] < 30), color='green', alpha=0.1)
            ax2.set_ylabel('RSI', color='purple')
            ax2.tick_params(axis='y', labelcolor='purple')
            ax2.set_ylim(0, 100)
        
        st.pyplot(fig)
        
        # Interpretasi indikator
        if 'RSI' in tech_df and not tech_df['RSI'].isnull().all():
            current_rsi = tech_df['RSI'].iloc[-1]
            st.subheader("Interpretasi Indikator")
            
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

with tab2:
    st.header(f"Berita & Sentimen {selected_coin}")
    
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
                
                st.subheader(f"Analisis Sentimen: {positive_count} 👍 vs {negative_count} 👎")
                
                # Progress bar sentimen
                sentiment_percent = int(sentiment_score * 100)
                st.progress(sentiment_percent / 100)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Persentase Positif", f"{sentiment_percent}%")
                with col2:
                    st.metric("Total Berita", len(sentiment_results))
                
                st.divider()
                
                # Tampilkan berita
                st.subheader("Berita Terkini")
                for i, result in enumerate(sentiment_results, 1):
                    sentiment_icon = "✅" if result['sentiment'] == 'POSITIVE' else "❌"
                    sentiment_color = "green" if result['sentiment'] == 'POSITIVE' else "red"
                    
                    with st.expander(f"{i}. {sentiment_icon} {result['title']}", expanded=False):
                        # Header berita
                        st.markdown(f"**Sumber:** {result.get('source', 'Tidak diketahui')}")
                        st.markdown(f"**Waktu:** {result.get('published_at', '')}")
                        
                        # Skor sentimen
                        st.markdown(f"**Sentimen:** :{sentiment_color}[{result['sentiment']}] (Skor: {result['score']:.2f})")
                        
                        # Reaksi komunitas
                        if result.get('votes'):
                            votes = result['votes']
                            st.markdown("**Reaksi Komunitas:**")
                            cols = st.columns(4)
                            with cols[0]:
                                st.metric("👍 Positif", votes.get('positive', 0))
                            with cols[1]:
                                st.metric("👎 Negatif", votes.get('negative', 0))
                            with cols[2]:
                                st.metric("⭐ Penting", votes.get('important', 0))
                            with cols[3]:
                                st.metric("💬 Komentar", votes.get('comments', 0))
                        
                        # Link berita
                        st.markdown(f"[Baca selengkapnya]({result['url']})")

with tab3:
    st.header(f"Rekomendasi Trading {selected_coin}")
    
    if st.button("Buat Analisis & Rekomendasi", type="primary"):
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
            st.subheader("📈 Analisis Kondisi Pasar")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Harga Saat Ini", f"${current_price:,.2f}")
            with col2:
                st.metric("Perubahan 24 Jam", f"{price_change:.2f}%")
            with col3:
                st.metric("RSI Terkini", f"{current_rsi:.1f}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Sentimen Positif", f"{sentiment_score*100:.1f}%")
                if sentiment_score > 0.7:
                    st.success("✅ Sentimen pasar sangat positif")
                elif sentiment_score < 0.3:
                    st.error("❌ Sentimen pasar sangat negatif")
                else:
                    st.info("➖ Sentimen pasar netral")
            
            with col2:
                st.metric("Volume 24 Jam", f"${coin_data['total_volume']/1e6:,.2f}M")
                st.metric("Market Cap", f"${coin_data['market_cap']/1e9:,.2f}B")
            
            st.divider()
            
            # Rekomendasi trading
            st.subheader("💡 Rekomendasi Trading")
            
            if current_rsi < 35 and sentiment_score > 0.65:
                # PERBAIKAN: Perhitungan tingkat kepercayaan yang benar
                rsi_factor = max(0, 35 - current_rsi)
                sentiment_factor = max(0, (sentiment_score - 0.65) * 30)
                confidence = min(85 + rsi_factor + sentiment_factor, 95)
                confidence = int(round(confidence))
                
                st.success("**REKOMENDASI: BELI**")
                st.metric("Tingkat Kepercayaan", f"{confidence}%")
                st.write("**Alasan:**")
                st.write("- Kondisi RSI menunjukkan oversold (harga mungkin terlalu rendah)")
                st.write("- Sentimen pasar sangat positif")
                st.write("- Potensi kenaikan harga dalam jangka pendek")
                
            elif current_rsi > 70 and sentiment_score < 0.4:
                # PERBAIKAN: Perhitungan tingkat kepercayaan yang benar
                rsi_factor = max(0, current_rsi - 70)
                sentiment_factor = max(0, (0.4 - sentiment_score) * 30)
                confidence = min(80 + rsi_factor + sentiment_factor, 95)
                confidence = int(round(confidence))
                
                st.error("**REKOMENDASI: JUAL**")
                st.metric("Tingkat Kepercayaan", f"{confidence}%")
                st.write("**Alasan:**")
                st.write("- Kondisi RSI menunjukkan overbought (harga mungkin terlalu tinggi)")
                st.write("- Sentimen pasar negatif")
                st.write("- Potensi koreksi harga dalam jangka pendek")
                
            else:
                confidence = 70
                st.info("**REKOMENDASI: TAHAN**")
                st.metric("Tingkat Kepercayaan", f"{confidence}%")
                st.write("**Alasan:**")
                st.write("- Tidak ada sinyal kuat untuk membeli atau menjual")
                st.write("- Pasar sedang dalam kondisi netral")
                st.write("- Pantau pergerakan harga untuk sinyal berikutnya")
            
            st.divider()
            
            # Grafik indikator
            st.subheader("Visualisasi Kondisi Pasar")
            
            fig, ax = plt.subplots(figsize=(10, 4))
            
            # Plot garis sentimen
            ax.plot([0, 1], [sentiment_score, sentiment_score], 'b-', linewidth=3, label='Sentimen')
            ax.plot([0.3, 0.3], [0, 1], 'r--', alpha=0.5, label='Batas Negatif')
            ax.plot([0.7, 0.7], [0, 1], 'g--', alpha=0.5, label='Batas Positif')
            
            # Plot titik RSI
            ax.plot(0.5, current_rsi/100, 'ro', markersize=10, label='RSI')
            
            ax.set_title('Visualisasi Sentimen vs RSI')
            ax.set_xlabel('Sentimen Pasar')
            ax.set_ylabel('RSI (skala 0-1)')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.legend()
            ax.grid(True)
            
            st.pyplot(fig)

# Footer
st.divider()
st.info("""
**📌 Tentang Crypto Analyst Pro:**
- **Sumber Data:** CoinGecko API + CryptoPanic API
- **Analisis:** Teknikal + Sentimen + AI
- **Update:** Data diperbarui secara berkala
- **Penggunaan:** Gratis 100%
""")
st.caption(f"Terakhir diperbarui: {datetime.now().strftime('%d %B %Y %H:%M')}")
