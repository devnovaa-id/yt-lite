from binance import Client, BinanceSocketManager
import pandas as pd
import numpy as np
import pywt
import talib
import time
import logging
from typing import Dict, Optional, Tuple

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crypto_trading.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("CryptoTrader")

class CryptoTradingSystem:
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, testnet: bool = False):
        self.client = Client(api_key, api_secret, testnet=testnet)
        self.socket_manager = BinanceSocketManager(self.client)
        self.active_sockets = {}
        logger.info("Trading system initialized")
    
    def get_klines(self, symbol: str, interval: str, limit: int = 500) -> pd.DataFrame:
        """Mendapatkan data klines dari Binance"""
        interval_map = {
            'M1': Client.KLINE_INTERVAL_1MINUTE,
            'M3': Client.KLINE_INTERVAL_3MINUTE,
            'M5': Client.KLINE_INTERVAL_5MINUTE,
            'M15': Client.KLINE_INTERVAL_15MINUTE,
            'M30': Client.KLINE_INTERVAL_30MINUTE,
            'H1': Client.KLINE_INTERVAL_1HOUR,
            'H4': Client.KLINE_INTERVAL_4HOUR,
            'D1': Client.KLINE_INTERVAL_1DAY
        }
        binance_interval = interval_map.get(interval, interval)
        
        try:
            klines = self.client.get_klines(
                symbol=symbol,
                interval=binance_interval,
                limit=limit
            )
            
            data = []
            for k in klines:
                data.append({
                    'timestamp': pd.to_datetime(k[0], unit='ms'),
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5]),
                    'close_time': pd.to_datetime(k[6], unit='ms'),
                    'quote_volume': float(k[7]),
                    'trades': int(k[8]),
                    'taker_buy_base': float(k[9]),
                    'taker_buy_quote': float(k[10])
                })
            
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error fetching klines: {e}")
            return pd.DataFrame()
    
    def calculate_indicators(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """Menghitung semua indikator teknis dan rekomendasi trading"""
        if df.empty or len(df) < 100:
            logger.warning("Insufficient data for indicator calculation")
            return df, {}
        
        try:
            close = df['close'].values
            high = df['high'].values
            low = df['low'].values
            volume = df['volume'].values
            
            # 1. Trend Detection (EMA)
            ema_fast = talib.EMA(close, timeperiod=9)
            ema_slow = talib.EMA(close, timeperiod=21)
            trend_up = ema_fast > ema_slow
            trend_down = ema_fast < ema_slow
            
            # 2. Momentum (RSI)
            rsi = talib.RSI(close, timeperiod=7)
            momentum_buy = (rsi < 40) & (np.diff(rsi, prepend=rsi[0]) > 0)
            momentum_sell = (rsi > 60) & (np.diff(rsi, prepend=rsi[0]) < 0)
            
            # 3. Trend Strength (ADX)
            adx = talib.ADX(high, low, close, timeperiod=14)
            trend_strong = adx > 20
            
            # 4. Volatility (ATR)
            atr = talib.ATR(high, low, close, timeperiod=14)
            valid_volatility = (high - low) > (0.8 * atr)
            
            # 5. Volume Spike
            vol_sma = talib.SMA(volume, timeperiod=20)
            volume_spike = volume > (1.5 * vol_sma)
            
            # 6. Candlestick Confirmation
            bull_candle = (close > df['open']) & ((close - df['open']) > (np.roll(close, 1) - np.roll(df['open'], 1)))
            bear_candle = (close < df['open']) & ((df['open'] - close) > (np.roll(df['open'], 1) - np.roll(close, 1)))
            
            # 7. Wavelet-MACD (Pro 2025)
            p_fast, p_slow, p_signal = self.optimize_macd_params(close)
            ema_fast_macd = talib.EMA(close, timeperiod=p_fast)
            ema_slow_macd = talib.EMA(close, timeperiod=p_slow)
            dif_raw = ema_fast_macd - ema_slow_macd
            dif_deno = self.wavelet_denoise(dif_raw)
            dea = talib.EMA(dif_deno, timeperiod=p_signal)
            macd_buy = (np.roll(dif_deno, 1) < np.roll(dea, 1)) & (dif_deno > dea)
            macd_sell = (np.roll(dif_deno, 1) > np.roll(dea, 1)) & (dif_deno < dea)
            
            # 8. Dynamic Grid Trading (DGT)
            window = min(60, len(close))
            highest_high = talib.MAX(high, window)
            lowest_low = talib.MIN(low, window)
            center = (highest_high + lowest_low) / 2
            spacing = atr
            grid_low = center - spacing
            grid_up = center + spacing
            grid_buy = close <= grid_low
            grid_sell = close >= grid_up
            
            # 9. Trading Recommendation
            buy_conditions = (
                trend_up & 
                momentum_buy & 
                trend_strong & 
                valid_volatility & 
                volume_spike & 
                bull_candle & 
                (macd_buy | grid_buy)
            )
            
            sell_conditions = (
                trend_down & 
                momentum_sell & 
                trend_strong & 
                valid_volatility & 
                volume_spike & 
                bear_candle & 
                (macd_sell | grid_sell)
            )
            
            recommendation = np.where(
                buy_conditions, 
                "BUY SEKARANG", 
                np.where(
                    sell_conditions, 
                    "SELL SEKARANG", 
                    "TUNGGU / NO TRADE"
                )
            )
            
            # 10. Risk Management
            atr_current = atr[-1] if len(atr) > 0 else 0
            last_close = close[-1] if len(close) > 0 else 0
            
            stop_loss_buy = last_close - (0.5 * atr_current)
            take_profit_buy = last_close + (1.5 * atr_current)
            
            stop_loss_sell = last_close + (0.5 * atr_current)
            take_profit_sell = last_close - (1.5 * atr_current)
            
            # Add indicators to DataFrame
            df['EMA_FAST'] = ema_fast
            df['EMA_SLOW'] = ema_slow
            df['RSI'] = rsi
            df['ADX'] = adx
            df['ATR'] = atr
            df['VOL_SMA'] = vol_sma
            df['DIF'] = dif_deno
            df['DEA'] = dea
            df['MACD'] = dif_deno - dea
            df['CENTER'] = center
            df['GRID_LOW'] = grid_low
            df['GRID_UP'] = grid_up
            df['RECOMMENDATION'] = recommendation
            
            # Analysis summary
            analysis = {
                'symbol': symbol,
                'last_close': last_close,
                'atr': atr_current,
                'trend_up': bool(trend_up[-1]),
                'trend_down': bool(trend_down[-1]),
                'momentum_buy': bool(momentum_buy[-1]),
                'momentum_sell': bool(momentum_sell[-1]),
                'trend_strong': bool(trend_strong[-1]),
                'valid_volatility': bool(valid_volatility[-1]),
                'volume_spike': bool(volume_spike[-1]),
                'bull_candle': bool(bull_candle[-1]),
                'bear_candle': bool(bear_candle[-1]),
                'macd_buy': bool(macd_buy[-1]),
                'macd_sell': bool(macd_sell[-1]),
                'grid_buy': bool(grid_buy[-1]),
                'grid_sell': bool(grid_sell[-1]),
                'recommendation': recommendation[-1],
                'stop_loss_buy': stop_loss_buy,
                'take_profit_buy': take_profit_buy,
                'stop_loss_sell': stop_loss_sell,
                'take_profit_sell': take_profit_sell
            }
            
            return df, analysis
        except Exception as e:
            logger.exception(f"Error in indicator calculation: {e}")
            return df, {}
    
    def wavelet_denoise(self, signal: np.ndarray, wavelet: str = 'db4', level: int = 3) -> np.ndarray:
        """Wavelet denoising menggunakan Daubechies-4 wavelet"""
        if len(signal) < 10:
            return signal
            
        try:
            # Dekomposisi sinyal
            coeffs = pywt.wavedec(signal, wavelet, level=level)
            
            # Hitung threshold (universal threshold)
            sigma = np.median(np.abs(coeffs[-level])) / 0.6745
            threshold = sigma * np.sqrt(2 * np.log(len(signal)))
            
            # Terapkan soft thresholding ke detail coefficients
            coeffs[1:] = [pywt.threshold(c, threshold, 'soft') for c in coeffs[1:]]
            
            # Rekonstruksi sinyal
            denoised = pywt.waverec(coeffs, wavelet)
            return denoised[:len(signal)]
        except Exception as e:
            logger.error(f"Wavelet denoising failed: {e}")
            return signal
    
    def optimize_macd_params(self, close: np.ndarray) -> Tuple[int, int, int]:
        """Optimasi parameter MACD dengan metode sederhana"""
        # Parameter default jika optimasi gagal
        default_params = (12, 26, 9)
        
        if len(close) < 100:
            logger.warning("Insufficient data for MACD optimization")
            return default_params
        
        try:
            best_fitness = -np.inf
            best_params = default_params
            
            # Ruang parameter
            fast_periods = [8, 9, 10, 11, 12]
            slow_periods = [22, 24, 26, 28]
            signal_periods = [7, 8, 9, 10]
            
            for fast in fast_periods:
                for slow in slow_periods:
                    if slow <= fast:
                        continue
                    for signal in signal_periods:
                        try:
                            ema_fast = talib.EMA(close, timeperiod=fast)
                            ema_slow = talib.EMA(close, timeperiod=slow)
                            dif = ema_fast - ema_slow
                            # Hapus nilai NaN
                            valid = ~np.isnan(dif)
                            dif = dif[valid]
                            if len(dif) == 0:
                                continue
                            dea = talib.EMA(dif, timeperiod=signal)
                            macd = dif - dea
                            
                            # Fungsi fitness: signal-to-noise ratio
                            std = np.std(macd)
                            if std == 0:
                                continue
                            fitness = np.mean(np.abs(macd)) / std
                            
                            if fitness > best_fitness:
                                best_fitness = fitness
                                best_params = (fast, slow, signal)
                        except:
                            continue
            
            logger.info(f"Optimized MACD params: {best_params} (fitness: {best_fitness:.2f})")
            return best_params
        except Exception as e:
            logger.error(f"MACD optimization failed: {e}")
            return default_params
    
    def get_trading_recommendation(self, symbol: str, interval: str, limit: int = 500) -> Dict:
        """Mendapatkan rekomendasi trading dengan manajemen risiko"""
        try:
            df = self.get_klines(symbol, interval, limit)
            if df.empty:
                return {"error": "No data available"}
            
            df, analysis = self.calculate_indicators(df)
            return analysis
        except Exception as e:
            logger.exception(f"Error in trading recommendation: {e}")
            return {"error": str(e)}
    
    def start_realtime(self, symbol: str, interval: str, callback):
        """Memulai analisis real-time dengan websocket"""
        interval_map = {
            'M1': Client.KLINE_INTERVAL_1MINUTE,
            'M3': Client.KLINE_INTERVAL_3MINUTE,
            'M5': Client.KLINE_INTERVAL_5MINUTE,
            'M15': Client.KLINE_INTERVAL_15MINUTE
        }
        binance_interval = interval_map.get(interval, interval)
        socket_name = f"{symbol.lower()}@{binance_interval}"
        
        # Hentikan socket yang ada jika ada
        if socket_name in self.active_sockets:
            self.stop_realtime(socket_name)
        
        # Mulai socket baru
        try:
            kline_socket = self.socket_manager.kline_socket(
                symbol=symbol, 
                interval=binance_interval
            )
            kline_socket.start()
            kline_socket.add_listener(callback)
            self.active_sockets[socket_name] = kline_socket
            logger.info(f"Started real-time socket for {symbol} @ {binance_interval}")
            return socket_name
        except Exception as e:
            logger.error(f"Failed to start real-time socket: {e}")
            return None
    
    def stop_realtime(self, socket_name: str):
        """Menghentikan analisis real-time"""
        if socket_name in self.active_sockets:
            try:
                self.active_sockets[socket_name].stop()
                del self.active_sockets[socket_name]
                logger.info(f"Stopped real-time socket: {socket_name}")
            except Exception as e:
                logger.error(f"Error stopping socket: {e}")
    
    def stop_all_realtime(self):
        """Menghentikan semua analisis real-time"""
        for name in list(self.active_sockets.keys()):
            self.stop_realtime(name)
    
    def __del__(self):
        self.stop_all_realtime()
