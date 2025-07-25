import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import time
from datetime import datetime

# Konfigurasi halaman
st.set_page_config(
    page_title="Cryptocurrency Dashboard",
    page_icon="💰",
    layout="wide"
)

# Fungsi ambil data dari API
def get_crypto_data():
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error mengambil data: {e}")
        return []

# Fungsi ambil data historis
def get_historical_data(coin_id, days=30):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
    try:
        data = requests.get(url, timeout=10).json()
        prices = data.get('prices', [])
        if not prices:
            return pd.DataFrame()
            
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except:
        return pd.DataFrame()

# Tampilan UI
st.title("💰 Cryptocurrency Dashboard")
st.write("Analisis data cryptocurrency menggunakan CoinGecko API")

# Ambil data
with st.spinner('Mengambil data terbaru...'):
    crypto_data = get_crypto_data()

if not crypto_data:
    st.error("Gagal mengambil data cryptocurrency. Silakan coba lagi nanti.")
    st.stop()

# Konversi ke DataFrame
df = pd.DataFrame(crypto_data)
df = df[['id', 'name', 'symbol', 'current_price', 'market_cap', 'total_volume', 
         'price_change_percentage_24h', 'high_24h', 'low_24h']]

# Tampilkan data mentah
st.subheader("Top 20 Cryptocurrency berdasarkan Market Cap")
st.dataframe(df.sort_values('market_cap', ascending=False).head(20))

# Visualisasi 1: Top 10 Crypto by Market Cap
st.subheader("Top 10 Cryptocurrency berdasarkan Market Cap")
top_10 = df.nlargest(10, 'market_cap')

fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(top_10['name'], top_10['market_cap'] / 1e9)
ax.set_title('Market Capitalization (dalam Miliar USD)', fontsize=14)
ax.set_ylabel('Market Cap (USD)', fontsize=12)
ax.tick_params(axis='x', rotation=45)
ax.grid(axis='y', linestyle='--', alpha=0.7)

# Format sumbu Y
ax.yaxis.set_major_formatter('${x:,.0f}B')

st.pyplot(fig)

# Pilih cryptocurrency untuk analisis
st.sidebar.header("Analisis Detail")
selected_coin = st.sidebar.selectbox(
    "Pilih Cryptocurrency",
    df['name']
)

# Dapatkan ID coin yang dipilih
coin_data = df[df['name'] == selected_coin].iloc[0]
coin_id = coin_data['id']

# Tampilkan metrik
st.sidebar.subheader(f"Statistik {selected_coin}")
st.sidebar.metric("Harga Saat Ini", f"${coin_data['current_price']:,.2f}")
st.sidebar.metric("Perubahan 24 Jam", f"{coin_data['price_change_percentage_24h']:.2f}%")
st.sidebar.metric("Market Cap", f"${coin_data['market_cap']/1e9:,.2f}B")
st.sidebar.metric("Volume 24 Jam", f"${coin_data['total_volume']/1e6:,.2f}M")

# Analisis data historis
st.subheader(f"Perubahan Harga {selected_coin}")
days = st.slider("Jumlah Hari", min_value=7, max_value=90, value=30)

with st.spinner('Mengambil data historis...'):
    historical_df = get_historical_data(coin_id, days)

if historical_df.empty:
    st.warning(f"Tidak dapat mengambil data historis untuk {selected_coin}")
else:
    # Grafik harga historis
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    ax2.plot(historical_df['date'], historical_df['price'], color='royalblue', linewidth=2)
    ax2.set_title(f'Perubahan Harga {selected_coin} ({days} Hari Terakhir)', fontsize=14)
    ax2.set_xlabel('Tanggal', fontsize=12)
    ax2.set_ylabel('Harga (USD)', fontsize=12)
    ax2.grid(True, linestyle='--', alpha=0.7)
    
    # Format sumbu Y
    ax2.yaxis.set_major_formatter('${x:,.0f}')
    
    # Rotasi label tanggal
    plt.xticks(rotation=45)
    
    st.pyplot(fig2)

# Footer
st.divider()
st.info("""
**📊 Sumber Data:** CoinGecko API (free tier)  
**🔄 Update Otomatis:** Data diperbarui setiap kali halaman dimuat ulang  
**⭐ Fitur Unggulan:**
- Top 100 cryptocurrency berdasarkan market cap
- Visualisasi interaktif
- Analisis harga historis
- Tampilan data real-time
""")
st.caption(f"Terakhir diperbarui: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
