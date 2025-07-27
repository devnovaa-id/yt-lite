import requests
import pandas as pd
import numpy as np
from transformers import pipeline
from datetime import datetime, timedelta
import yfinance as yf
from binance.client import Client
import time

# Konfigurasi API
CRYPTO_PANIC_API_KEY = "d3b14a16db908837c9058ebffadf852f6cf7a269"
BINANCE_API_KEY = "w8AKRjpvU1yp0dmkQrdNhcnQ5Y7bEKzNIYS9qjjYiaoB3lmDg6CW4h01UGIji3oi"
BINANCE_API_SECRET = "KnLbMX5QWtd16kFYGVHDQUFrPCJnqwi4QOWfllSSEsjB5oKtvj7F96XziG9eDBMf"

# Simbol aset
ASSET_METADATA = {
    "XAUUSD": {
        "yfinance": "GC=F",
        "binance": "XAUUSD",
        "name": "Gold (XAU/USD)",
        "type": "commodity"
    },
    "BTCUSD": {
        "yfinance": "BTC-USD",
        "binance": "BTCUSDT",
        "name": "Bitcoin (BTC/USD)",
        "type": "crypto"
    },
    "USOIL": {
        "yfinance": "CL=F",
        "binance": "USOIL",
        "name": "Crude Oil (USOIL)",
        "type": "commodity"
    }
}

# Inisialisasi klien Binance
binance_client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

def load_ai_models():
    """Muat model AI untuk analisis sentimen"""
    try:
        sentiment_model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
        return sentiment_model
    except Exception as e:
        print(f"Gagal memuat model AI: {e}")
        return None

def get_asset_data():
    """Ambil data aset terbaru menggunakan Binance dan yfinance"""
    assets = []
    
    for symbol, meta in ASSET_METADATA.items():
        try:
            # Untuk kripto, gunakan Binance untuk data real-time
            if meta["type"] == "crypto":
                ticker = binance_client.get_symbol_ticker(symbol=meta["binance"])
                price = float(ticker['price'])
                
                # Dapatkan data 24 jam
                stats = binance_client.get_ticker(symbol=meta["binance"])
                change_pct = float(stats['priceChangePercent'])
                high = float(stats['highPrice'])
                low = float(stats['lowPrice'])
                volume = float(stats['volume'])
                
            # Untuk komoditas, gunakan yfinance
            else:
                yf_ticker = yf.Ticker(meta["yfinance"])
                data = yf_ticker.history(period="1d")
                
                if data.empty:
                    continue
                
                price = data['Close'].iloc[-1]
                prev_close = data['Close'].iloc[-2] if len(data) > 1 else price
                change_pct = ((price - prev_close) / prev_close) * 100
                high = data['High'].max()
                low = data['Low'].min()
                volume = data['Volume'].iloc[-1]
            
            assets.append({
                'symbol': symbol,
                'name': meta["name"],
                'current_price': price,
                'price_change_percentage_24h': change_pct,
                'high_24h': high,
                'low_24h': low,
                'volume': volume,
                'type': meta["type"]
            })
        except Exception as e:
            print(f"Error mengambil data {symbol}: {e}")
            # Fallback ke yfinance jika Binance gagal
            try:
                yf_ticker = yf.Ticker(meta["yfinance"])
                data = yf_ticker.history(period="1d")
                
                if not data.empty:
                    price = data['Close'].iloc[-1]
                    prev_close = data['Close'].iloc[-2] if len(data) > 1 else price
                    change_pct = ((price - prev_close) / prev_close) * 100
                    
                    assets.append({
                        'symbol': symbol,
                        'name': meta["name"],
                        'current_price': price,
                        'price_change_percentage_24h': change_pct,
                        'high_24h': data['High'].max(),
                        'low_24h': data['Low'].min(),
                        'volume': data['Volume'].iloc[-1],
                        'type': meta["type"]
                    })
            except:
                print(f"Fallback untuk {symbol} juga gagal")
    
    return assets

def get_historical_data(symbol, days=365):
    """Ambil data historis menggunakan Binance (untuk kripto) atau yfinance (untuk komoditas)"""
    try:
        meta = ASSET_METADATA[symbol]
        
        # Untuk kripto, gunakan Binance
        if meta["type"] == "crypto":
            # Dapatkan data kline (candlestick)
            klines = binance_client.get_historical_klines(
                symbol=meta["binance"],
                interval=Client.KLINE_INTERVAL_1DAY,
                limit=days
            )
            
            # Proses data kline
            data = []
            for k in klines:
                timestamp = datetime.fromtimestamp(k[0] / 1000)
                data.append({
                    'Date': timestamp,
                    'price': float(k[4])  # Close price
                })
                
            df = pd.DataFrame(data)
            return df
        
        # Untuk komoditas, gunakan yfinance
        else:
            ticker = yf.Ticker(meta["yfinance"])
            df = ticker.history(period=f"{days}d")
            
            if df.empty:
                return pd.DataFrame()
                
            df.reset_index(inplace=True)
            df.rename(columns={'Close': 'price'}, inplace=True)
            return df[['Date', 'price']]
            
    except Exception as e:
        print(f"Error data historis {symbol}: {e}")
        # Fallback ke yfinance
        try:
            ticker = yf.Ticker(meta["yfinance"])
            df = ticker.history(period=f"{days}d")
            
            if df.empty:
                return pd.DataFrame()
                
            df.reset_index(inplace=True)
            df.rename(columns={'Close': 'price'}, inplace=True)
            return df[['Date', 'price']]
        except:
            return pd.DataFrame()

def get_asset_news(asset_symbol):
    """Ambil berita untuk aset tertentu"""
    endpoint = "https://cryptopanic.com/api/v1/posts/"
    params = {
        "auth_token": CRYPTO_PANIC_API_KEY,
        "public": "true",
        "filter": "rising",
        "regions": "en",
        "kind": "news"
    }
    
    # Mapping simbol aset ke mata uang CryptoPanic
    currency_map = {
        "BTCUSD": "BTC",
        "XAUUSD": "XAU",
        "USOIL": "OIL"
    }
    
    if asset_symbol in currency_map:
        params["currencies"] = currency_map[asset_symbol]
    
    try:
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except Exception as e:
        print(f"Error mengambil berita: {e}")
        return []

def analyze_news_sentiment(news_items, sentiment_model):
    """Analisis sentimen dari berita"""
    if not news_items or not sentiment_model:
        return []
    
    results = []
    for item in news_items:
        title = item.get('title', '')
        if not title:
            continue
            
        try:
            sentiment = sentiment_model(title[:512])[0]
            results.append({
                'title': title,
                'sentiment': sentiment['label'],
                'score': sentiment['score'],
                'url': item.get('url', '#'),
                'source': item.get('source', {}).get('title', 'Unknown'),
                'published_at': item.get('published_at', ''),
                'votes': item.get('votes', {})
            })
        except Exception as e:
            print(f"Gagal menganalisis sentimen: {e}")
            continue
    
    return results

def calculate_technical_indicators(df):
    """Hitung indikator teknikal (SMA, RSI)"""
    try:
        # Pastikan data terurut
        df = df.sort_values('Date')
        
        # Moving averages
        df['SMA_7'] = df['price'].rolling(window=7).mean()
        df['SMA_30'] = df['price'].rolling(window=30).mean()
        
        # RSI
        delta = df['price'].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        
        # Hindari pembagian dengan nol
        avg_loss = avg_loss.replace(0, 0.001)
        
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df
    except Exception as e:
        print(f"Error indikator teknikal: {e}")
        return df

def generate_trading_recommendation(asset_data, tech_df, sentiment_results):
    """Hasilkan rekomendasi trading berdasarkan analisis"""
    if tech_df.empty:
        return "TAHAN", 50
    
    # Hitung skor sentimen
    sentiment_score = 0.5
    if sentiment_results:
        positive_count = sum(1 for r in sentiment_results if r['sentiment'] == 'POSITIVE')
        total_count = len(sentiment_results)
        sentiment_score = positive_count / total_count if total_count > 0 else 0.5
    
    # Nilai indikator
    current_price = asset_data['current_price']
    current_rsi = tech_df['RSI'].iloc[-1] if 'RSI' in tech_df.columns else 50
    
    # Logika rekomendasi khusus untuk masing-masing aset
    if asset_data['symbol'] == "XAUUSD":  # Emas
        if current_rsi < 30:
            return "BELI", 80
        elif current_rsi > 70:
            return "JUAL", 75
        else:
            return "TAHAN", 65
    
    elif asset_data['symbol'] == "BTCUSD":  # Bitcoin
        if current_rsi < 35 and sentiment_score > 0.6:
            return "BELI", 85
        elif current_rsi > 70 and sentiment_score < 0.4:
            return "JUAL", 80
        else:
            return "TAHAN", 70
    
    elif asset_data['symbol'] == "USOIL":  # Minyak
        if current_rsi < 30:
            return "BELI", 75
        elif current_rsi > 75:
            return "JUAL", 80
        else:
            return "TAHAN", 60
    
    return "TAHAN", 50
