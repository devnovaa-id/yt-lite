import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
from transformers import pipeline
from sklearn.linear_model import LinearRegression
import json

# Konfigurasi API
CRYPTO_PANIC_API_KEY = "d3b14a16db908837c9058ebffadf852f6cf7a269"
COINGECKO_API_KEY = "CG-fGwadP1e3em6BHmDUdEkecD7"
CRYPTO_PANIC_BASE_URL = "https://cryptopanic.com/api/developer/v2"

# Konfigurasi halaman
st.set_page_config(
    page_title="🤖 AI Crypto Analyst Pro",
    page_icon="🤖",
    layout="wide"
)

# Inisialisasi model AI
@st.cache_resource
def load_ai_models():
    sentiment_model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    return sentiment_model

# Fungsi untuk mendapatkan data crypto dari CoinGecko
@st.cache_data(ttl=300)
def get_crypto_data():
    base_url = "https://api.coingecko.com/api/v3"
    endpoint = f"/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false&x_cg_demo_api_key={COINGECKO_API_KEY}"
    
    try:
        response = requests.get(base_url + endpoint, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error mengambil data: {e}")
        return []

# Fungsi untuk mendapatkan data historis
@st.cache_data(ttl=3600)
def get_historical_data(coin_id, days=365):
    base_url = "https://api.coingecko.com/api/v3"
    endpoint = f"/coins/{coin_id}/market_chart?vs_currency=usd&days={days}&x_cg_demo_api_key={COINGECKO_API_KEY}"
    
    try:
        data = requests.get(base_url + endpoint, timeout=15).json()
        prices = data.get('prices', [])
        if not prices:
            return pd.DataFrame()
            
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df[['date', 'price']]
    except Exception as e:
        st.error(f"Error mengambil data historis: {e}")
        return pd.DataFrame()

# Fungsi untuk mendapatkan berita dari CryptoPanic
@st.cache_data(ttl=600)
def get_crypto_news(coin_symbol=None, filter_type="rising", public=True):
    endpoint = f"{CRYPTO_PANIC_BASE_URL}/posts/"
    params = {
        "auth_token": CRYPTO_PANIC_API_KEY,
        "public": "true" if public else "false",
        "filter": filter_type,
        "regions": "en",
        "kind": "news"
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

# Fungsi untuk analisis sentimen menggunakan AI
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
                'id': item.get('id'),
                'title': title,
                'sentiment': sentiment['label'],
                'score': sentiment['score'],
                'url': item.get('url', '#'),
                'source': item.get('source', {}).get('title', 'Unknown'),
                'published_at': item.get('published_at', ''),
                'votes': item.get('votes', {})
            })
        except Exception as e:
            st.error(f"Error analisis sentimen: {e}")
    
    return results

# Fungsi untuk prediksi harga menggunakan AI
def predict_price_with_ai(df, days_to_predict=30):
    try:
        df = df.copy()
        df['days'] = (df['date'] - df['date'].min()).dt.days
        X = df[['days']].values
        y = df['price'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        future_days = np.array(range(df['days'].max() + 1, df['days'].max() + days_to_predict + 1))
        future_dates = [df['date'].max() + timedelta(days=i) for i in range(1, days_to_predict + 1)]
        predicted_prices = model.predict(future_days.reshape(-1, 1))
        
        return future_dates, predicted_prices
    except Exception as e:
        st.error(f"Error prediksi AI: {e}")
        return [], []

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
    except Exception as e:
        st.error(f"Error perhitungan indikator: {e}")
        return df

# Fungsi untuk analisis sentimen pasar
def get_market_sentiment():
    try:
        news_items = get_crypto_news(filter_type="hot")
        if not news_items:
            return 0.5, 0, 0, 0  # Netral jika tidak ada data
        
        positive = 0
        negative = 0
        important = 0
        
        for item in news_items:
            votes = item.get('votes', {})
            positive += votes.get('positive', 0)
            negative += votes.get('negative', 0)
            important += votes.get('important', 0)
        
        total_votes = positive + negative
        if total_votes == 0:
            return 0.5, positive, negative, important
            
        sentiment_score = positive / total_votes
        return sentiment_score, positive, negative, important
    except:
        return 0.5, 0, 0, 0

# Tampilan UI
st.title("🤖 AI Crypto Analyst Pro")
st.markdown("""
### Platform Analisis Cryptocurrency Berbasis AI
Analisis prediktif, sentimen pasar, dan indikator teknikal berbasis AI
""")

# Ambil model AI
sentiment_model = load_ai_models()

# Sidebar - Analisis Pasar
st.sidebar.header("📊 Analisis Pasar")

# Analisis sentimen pasar secara real-time
with st.sidebar.expander("📈 Sentimen Pasar"):
    sentiment_score, positive, negative, important = get_market_sentiment()
    sentiment_percent = int(sentiment_score * 100)
    
    st.metric("Skor Sentimen Pasar", f"{sentiment_percent}%")
    st.progress(sentiment_percent / 100)
    
    if sentiment_score > 0.7:
        st.success("✅ Sentimen pasar sangat positif")
    elif sentiment_score < 0.3:
        st.error("❌ Sentimen pasar sangat negatif")
    else:
        st.info("➖ Sentimen pasar netral")
    
    st.divider()
    st.metric("Votes Positif", positive)
    st.metric("Votes Negatif", negative)
    st.metric("Berita Penting", important)

# Top 5 Berita Terkini
with st.sidebar.expander("📰 Berita Terkini"):
    market_news = get_crypto_news(filter_type="rising")[:5]
    for item in market_news:
        title = item.get('title', 'No title')
        source = item.get('source', {}).get('title', 'Unknown')
        
        st.markdown(f"**{title}**")
        st.caption(f"Sumber: {source}")
        
        # Tampilkan votes jika ada
        if 'votes' in item:
            votes = item['votes']
            cols = st.columns(3)
            with cols[0]:
                st.metric("👍", votes.get('positive', 0))
            with cols[1]:
                st.metric("👎", votes.get('negative', 0))
            with cols[2]:
                st.metric("⭐", votes.get('important', 0))
        
        st.markdown(f"[Baca selengkapnya]({item.get('url', '#')})")
        st.divider()

# Ambil data crypto
with st.spinner('Mengambil data terbaru...'):
    crypto_data = get_crypto_data()

if not crypto_data:
    st.error("Gagal mengambil data cryptocurrency. Silakan coba lagi nanti.")
    st.stop()

# Konversi ke DataFrame
df_coins = pd.DataFrame(crypto_data)
df_coins = df_coins[['id', 'name', 'symbol', 'current_price', 'market_cap', 'total_volume', 
                     'price_change_percentage_24h', 'high_24h', 'low_24h']]

# Tampilkan data utama
st.subheader("📊 Top 20 Cryptocurrency Berdasarkan Market Cap")
df_display = df_coins.sort_values('market_cap', ascending=False).head(20).copy()
df_display = df_display.rename(columns={
    'current_price': 'Harga',
    'market_cap': 'Market Cap',
    'total_volume': 'Volume 24h',
    'price_change_percentage_24h': 'Perubahan 24h'
})

st.dataframe(df_display.style.format({
    'Harga': '${:,.2f}',
    'Market Cap': '${:,.0f}',
    'Volume 24h': '${:,.0f}',
    'Perubahan 24h': '{:.2f}%'
}))

# Pilih cryptocurrency untuk analisis
st.sidebar.header("🔍 Analisis Detail")
selected_coin = st.sidebar.selectbox(
    "Pilih Cryptocurrency",
    df_coins['name']
)

# Dapatkan data coin yang dipilih
coin_data = df_coins[df_coins['name'] == selected_coin].iloc[0]
coin_id = coin_data['id']
coin_symbol = coin_data['symbol']

# Tampilkan metrik
st.sidebar.subheader(f"📈 Statistik {selected_coin}")
st.sidebar.metric("Harga Saat Ini", f"${coin_data['current_price']:,.2f}")
st.sidebar.metric("Perubahan 24 Jam", f"{coin_data['price_change_percentage_24h']:.2f}%")
st.sidebar.metric("Market Cap", f"${coin_data['market_cap']/1e9:,.2f}B")
st.sidebar.metric("Volume 24 Jam", f"${coin_data['total_volume']/1e6:,.2f}M")

# Tab untuk berbagai jenis analisis
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Analisis Teknikal", 
    "🔮 Prediksi AI", 
    "📰 Sentimen Pasar", 
    "💡 Rekomendasi AI"
])

with tab1:
    st.subheader(f"📈 Analisis Teknikal {selected_coin}")
    days = st.slider("Jumlah Hari Historis", min_value=30, max_value=365, value=90)
    
    with st.spinner('Mengambil data historis...'):
        historical_df = get_historical_data(coin_id, days)
    
    if historical_df.empty:
        st.warning(f"Tidak dapat mengambil data historis untuk {selected_coin}")
    else:
        # Hitung indikator teknikal
        tech_df = calculate_technical_indicators(historical_df)
        
        # Plot harga dan moving averages
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(tech_df['date'], tech_df['price'], label='Harga', color='blue')
        ax.plot(tech_df['date'], tech_df['SMA_7'], label='SMA 7 Hari', color='orange')
        ax.plot(tech_df['date'], tech_df['SMA_30'], label='SMA 30 Hari', color='green')
        ax.set_title(f'Analisis Teknikal: {selected_coin}', fontsize=16)
        ax.set_xlabel('Tanggal')
        ax.set_ylabel('Harga (USD)')
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)
        
        # Plot RSI
        st.subheader("Relative Strength Index (RSI)")
        fig2, ax2 = plt.subplots(figsize=(12, 4))
        ax2.plot(tech_df['date'], tech_df['RSI'], label='RSI', color='purple')
        ax2.axhline(70, color='red', linestyle='--', label='Overbought (70)')
        ax2.axhline(30, color='green', linestyle='--', label='Oversold (30)')
        ax2.set_title('RSI (14 Hari)')
        ax2.legend()
        ax2.grid(True)
        st.pyplot(fig2)
        
        # Interpretasi RSI
        if 'RSI' in tech_df and not tech_df['RSI'].isnull().all():
            current_rsi = tech_df['RSI'].iloc[-1]
            if current_rsi > 70:
                st.warning("⚠️ Overbought: Potensi koreksi harga turun")
            elif current_rsi < 30:
                st.success("✅ Oversold: Potensi pemulihan harga naik")
            else:
                st.info("ℹ️ RSI dalam range normal")
        else:
            st.warning("Data RSI tidak tersedia")

with tab2:
    st.subheader(f"🔮 Prediksi Harga {selected_coin} dengan AI")
    st.info("Model AI menggunakan regresi linear untuk memprediksi tren harga jangka pendek")
    
    days_hist = st.slider("Data Historis untuk Training Model", min_value=60, max_value=365, value=180)
    days_predict = st.slider("Jumlah Hari Prediksi", min_value=7, max_value=90, value=30)
    
    if st.button("Jalankan Prediksi AI"):
        with st.spinner('Melatih model AI dan membuat prediksi...'):
            historical_df = get_historical_data(coin_id, days_hist)
            if historical_df.empty:
                st.error("Data historis tidak cukup untuk prediksi")
            else:
                future_dates, predicted_prices = predict_price_with_ai(historical_df, days_predict)
                
                if not future_dates:
                    st.error("Gagal membuat prediksi")
                else:
                    # Buat plot interaktif
                    fig = go.Figure()
                    
                    # Data historis
                    fig.add_trace(go.Scatter(
                        x=historical_df['date'],
                        y=historical_df['price'],
                        mode='lines',
                        name='Harga Historis',
                        line=dict(color='blue')
                    ))
                    
                    # Prediksi
                    fig.add_trace(go.Scatter(
                        x=future_dates,
                        y=predicted_prices,
                        mode='lines+markers',
                        name='Prediksi AI',
                        line=dict(color='green', dash='dash')
                    ))
                    
                    fig.update_layout(
                        title=f'Prediksi Harga {selected_coin}',
                        xaxis_title='Tanggal',
                        yaxis_title='Harga (USD)',
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Tampilkan prediksi dalam tabel
                    prediction_df = pd.DataFrame({
                        'Tanggal': future_dates,
                        'Prediksi Harga': predicted_prices
                    })
                    st.dataframe(prediction_df.style.format({
                        'Prediksi Harga': '${:,.2f}'
                    }))

with tab3:
    st.subheader(f"📰 Analisis Sentimen Pasar untuk {selected_coin}")
    
    # Filter berita
    col1, col2 = st.columns(2)
    with col1:
        filter_type = st.selectbox("Filter Berita", ["rising", "hot", "bullish", "bearish", "important"], index=0)
    with col2:
        limit = st.slider("Jumlah Berita", 5, 20, 10)
    
    if st.button("Analisis Sentimen Berita Terbaru"):
        with st.spinner('Mengambil dan menganalisis berita...'):
            # Dapatkan berita dari CryptoPanic
            news_items = get_crypto_news(coin_symbol=coin_symbol, filter_type=filter_type)[:limit]
            
            # Analisis sentimen dengan AI
            sentiment_results = analyze_news_sentiment(news_items, sentiment_model)
            
            if not sentiment_results:
                st.error("Tidak dapat mengambil atau menganalisis berita")
            else:
                positive_count = sum(1 for r in sentiment_results if r['sentiment'] == 'POSITIVE')
                negative_count = sum(1 for r in sentiment_results if r['sentiment'] == 'NEGATIVE')
                
                # Tampilkan ringkasan sentimen
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Berita Positif", positive_count)
                with col2:
                    st.metric("Berita Negatif", negative_count)
                
                # Plot sentimen
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.bar(['Positif', 'Negatif'], [positive_count, negative_count], color=['green', 'red'])
                ax.set_title('Distribusi Sentimen Berita')
                st.pyplot(fig)
                
                # Tampilkan detail berita
                st.subheader("Detail Analisis Sentimen:")
                for result in sentiment_results:
                    sentiment_icon = "✅" if result['sentiment'] == 'POSITIVE' else "❌"
                    votes = result.get('votes', {})
                    
                    with st.expander(f"{sentiment_icon} {result['title']}", expanded=False):
                        st.write(f"**Sumber:** {result.get('source', 'Tidak diketahui')}")
                        st.write(f"**Waktu Publikasi:** {result.get('published_at', '')}")
                        st.write(f"**Skor Sentimen:** {result['score']:.2f}")
                        
                        # Tampilkan votes jika ada
                        if votes:
                            st.write("**Reaksi Komunitas:**")
                            cols = st.columns(4)
                            with cols[0]:
                                st.metric("👍 Positif", votes.get('positive', 0))
                            with cols[1]:
                                st.metric("👎 Negatif", votes.get('negative', 0))
                            with cols[2]:
                                st.metric("⭐ Penting", votes.get('important', 0))
                            with cols[3]:
                                st.metric("💬 Komentar", votes.get('comments', 0))
                        
                        st.write(f"**Link:** [Baca berita]({result['url']})")

with tab4:
    st.subheader(f"💡 Rekomendasi AI untuk {selected_coin}")
    st.info("Rekomendasi berbasis analisis teknikal dan sentimen pasar")
    
    if st.button("Buat Rekomendasi"):
        with st.spinner('Menganalisis data dan membuat rekomendasi...'):
            # Dapatkan data historis
            historical_df = get_historical_data(coin_id, 90)
            
            if historical_df.empty:
                st.error("Tidak dapat membuat rekomendasi tanpa data historis")
            else:
                # Analisis teknikal
                tech_df = calculate_technical_indicators(historical_df)
                current_rsi = tech_df['RSI'].iloc[-1] if 'RSI' in tech_df and not tech_df.empty else 50
                
                # Analisis sentimen
                sentiment_results = analyze_news_sentiment(
                    get_crypto_news(coin_symbol=coin_symbol, filter_type="hot"), 
                    sentiment_model
                )
                positive_count = sum(1 for r in sentiment_results if r['sentiment'] == 'POSITIVE')
                total_count = len(sentiment_results) or 1
                sentiment_score = positive_count / total_count
                
                # Buat rekomendasi
                recommendation = ""
                confidence = 0
                reasoning = ""
                
                if current_rsi < 40 and sentiment_score > 0.6:
                    recommendation = "BELI"
                    confidence = min(85 + int((40 - current_rsi) * 0.5) + int((sentiment_score - 0.6) * 50), 95)
                    reasoning = f"Kondisi oversold (RSI: {current_rsi:.1f}) dan sentimen pasar positif ({sentiment_score*100:.1f}%)"
                elif current_rsi > 70 and sentiment_score < 0.4:
                    recommendation = "JUAL"
                    confidence = min(80 + int((current_rsi - 70) * 0.5) + int((0.4 - sentiment_score) * 50), 95)
                    reasoning = f"Kondisi overbought (RSI: {current_rsi:.1f}) dan sentimen pasar negatif ({sentiment_score*100:.1f}%)"
                else:
                    recommendation = "Tahan"
                    confidence = 75
                    reasoning = "Tidak ada sinyal kuat untuk membeli atau menjual"
                
                # Tampilkan hasil
                st.subheader(f"Rekomendasi: **{recommendation}**")
                st.metric("Tingkat Kepercayaan", f"{confidence}%")
                
                st.subheader("Alasan Rekomendasi:")
                st.write(reasoning)
                
                st.subheader("Faktor yang Dianalisis:")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("RSI Terkini", f"{current_rsi:.1f}")
                    if current_rsi < 40:
                        st.success("Kondisi Oversold")
                    elif current_rsi > 70:
                        st.warning("Kondisi Overbought")
                    else:
                        st.info("RSI dalam Range Normal")
                
                with col2:
                    st.metric("Skor Sentimen", f"{sentiment_score:.2f}/1.0")
                    if sentiment_score > 0.6:
                        st.success("Sentimen Positif")
                    elif sentiment_score < 0.4:
                        st.warning("Sentimen Negatif")
                    else:
                        st.info("Sentimen Netral")

# Footer
st.divider()
st.info("""
**🤖 Tentang AI Crypto Analyst Pro:**
- **Sumber Data:** CoinGecko API + CryptoPanic API
- **Fitur Analisis:** Prediksi harga AI + Analisis sentimen + Indikator teknikal
- **Update Real-time:** Data diperbarui setiap 5 menit
- **Gratis 100%:** Tanpa biaya berlangganan
""")
st.caption(f"Terakhir diperbarui: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
