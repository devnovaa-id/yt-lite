import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import time

# Konfigurasi halaman
st.set_page_config(
    page_title="Cryptocurrency Dashboard",
    page_icon="💰",
    layout="wide"
)

# Fungsi ambil data dari API
def get_crypto_data():
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false"
    response = requests.get(url)
    return response.json()

# Fungsi ambil data historis
def get_historical_data(coin_id, days=30):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
    data = requests.get(url).json()
    prices = data['prices']
    df = pd.DataFrame(prices, columns=['timestamp', 'price'])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

# Tampilan UI
st.title("💰 Cryptocurrency Dashboard")
st.write("Analisis data cryptocurrency menggunakan CoinGecko API")

# Ambil data
with st.spinner('Mengambil data terbaru...'):
    crypto_data = get_crypto_data()

# Konversi ke DataFrame
df = pd.DataFrame(crypto_data)
df = df[['id', 'name', 'symbol', 'current_price', 'market_cap', 'total_volume', 
         'price_change_percentage_24h', 'high_24h', 'low_24h']]

# Tampilkan data mentah
st.subheader("Data Pasar Crypto Live")
st.dataframe(df.sort_values('market_cap', ascending=False).head(20))

# Visualisasi 1: Top 10 Crypto by Market Cap
st.subheader("Top 10 Cryptocurrency berdasarkan Market Cap")
top_10 = df.nlargest(10, 'market_cap')
plt.figure(figsize=(10, 6))
plt.bar(top_10['name'], top_10['market_cap'] / 1e9)
plt.title('Market Capitalization (dalam Miliar USD)')
plt.xticks(rotation=45)
plt.ylabel('Market Cap (USD)')
st.pyplot(plt)

# Pilih cryptocurrency untuk analisis
st.sidebar.header("Analisis Detail")
selected_coin = st.sidebar.selectbox(
    "Pilih Cryptocurrency",
    df['name']
)

# Dapatkan ID coin yang dipilih
coin_id = df[df['name'] == selected_coin]['id'].values[0]

# Tampilkan metrik
st.sidebar.subheader(f"Statistik {selected_coin}")
coin_data = df[df['name'] == selected_coin].iloc[0]
st.sidebar.metric("Harga Saat Ini", f"${coin_data['current_price']:,.2f}")
st.sidebar.metric("Perubahan 24 Jam", f"{coin_data['price_change_percentage_24h']:.2f}%")
st.sidebar.metric("Market Cap", f"${coin_data['market_cap']/1e9:,.2f}B")
st.sidebar.metric("Volume 24 Jam", f"${coin_data['total_volume']/1e6:,.2f}M")

# Analisis data historis
st.subheader(f"Perubahan Harga {selected_coin}")
days = st.slider("Jumlah Hari", min_value=7, max_value=90, value=30)

with st.spinner('Mengambil data historis...'):
    historical_df = get_historical_data(coin_id, days)

# Grafik harga historis
plt.figure(figsize=(10, 6))
plt.plot(historical_df['date'], historical_df['price'])
plt.title(f'Perubahan Harga {selected_coin} ({days} Hari Terakhir)')
plt.xlabel('Tanggal')
plt.ylabel('Harga (USD)')
plt.grid(True)
st.pyplot(plt)

# Informasi tambahan
st.info("""
**Sumber Data:** CoinGecko API (free tier)  
**Update Otomatis:** Data diperbarui setiap kali halaman dimuat ulang  
**Fitur:**
- Top 100 cryptocurrency berdasarkan market cap
- Visualisasi sederhana
- Analisis harga historis
- Tampilan data real-time
""")
