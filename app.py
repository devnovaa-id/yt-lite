# app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import backend
import numpy as np

# Konfigurasi halaman
st.set_page_config(
    page_title="📈 Quantum Analyst Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Tailwind untuk tampilan minimalis dan profesional
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  --primary: #2563eb;
  --primary-dark: #1d4ed8;
  --secondary: #64748b;
  --background: #f8fafc;
  --card: #ffffff;
  --text: #0f172a;
}

* {
  font-family: 'Inter', sans-serif;
}

body {
  background-color: var(--background);
  color: var(--text);
}

h1, h2, h3, h4 {
  font-weight: 700;
  color: var(--text);
}

.stApp {
  background-color: var(--background);
}

/* Card styling */
.card {
  background-color: var(--card);
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  transition: all 0.3s ease;
  border: 1px solid #e2e8f0;
}

.card:hover {
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

/* Metric styling */
.metric-value {
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--primary);
}

.metric-label {
  font-size: 0.9rem;
  color: var(--secondary);
  margin-top: 0.25rem;
}

/* Button styling */
.stButton>button {
  background-color: var(--primary);
  color: white;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-weight: 600;
  transition: all 0.3s ease;
  border: none;
}

.stButton>button:hover {
  background-color: var(--primary-dark);
  transform: scale(1.03);
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
  gap: 8px;
}

.stTabs [data-baseweb="tab"] {
  background-color: #e2e8f0;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  transition: all 0.3s ease;
  font-weight: 500;
  margin: 0 4px;
}

.stTabs [aria-selected="true"] {
  background-color: var(--primary);
  color: white;
}

/* Custom progress bar */
.stProgress > div > div > div {
  background-color: var(--primary);
}

/* Custom select boxes */
.stSelectbox div[data-baseweb="select"] {
  border-radius: 8px;
  border: 1px solid #cbd5e1;
}

/* Custom sliders */
.stSlider .thumb {
  background-color: var(--primary);
  border: none;
}

.stSlider .track {
  background-color: #cbd5e1;
}

.stSlider .track-0 {
  background-color: var(--primary);
}

/* Footer styling */
.footer {
  margin-top: 3rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e2e8f0;
  color: var(--secondary);
  font-size: 0.9rem;
}

/* Custom tooltips */
.tooltip-box {
  position: relative;
  display: inline-block;
  cursor: pointer;
}

.tooltip-box .tooltip-text {
  visibility: hidden;
  width: 200px;
  background-color: var(--text);
  color: var(--card);
  text-align: center;
  border-radius: 6px;
  padding: 8px;
  position: absolute;
  z-index: 1;
  bottom: 125%;
  left: 50%;
  transform: translateX(-50%);
  opacity: 0;
  transition: opacity 0.3s;
  font-size: 0.85rem;
  font-weight: normal;
}

.tooltip-box:hover .tooltip-text {
  visibility: visible;
  opacity: 1;
}
</style>
""", unsafe_allow_html=True)

# Header aplikasi
st.markdown("""
<div class="flex flex-col items-center mb-8">
  <h1 class="text-3xl font-bold text-center">📈 Quantum Analyst Pro</h1>
  <p class="text-center text-secondary mt-2">Advanced Technical Analysis for XAUUSD, BTCUSD & USOIL</p>
</div>
""", unsafe_allow_html=True)

# Ambil model AI
sentiment_model = backend.load_ai_models()

# Dapatkan data aset
asset_data = backend.get_asset_data()
asset_symbols = [asset['symbol'] for asset in asset_data]

# Sidebar - Pemilihan Aset
with st.sidebar:
    st.markdown('<h2 class="text-xl font-bold mb-4">🔍 Select Asset</h2>', unsafe_allow_html=True)
    
    # Pilih aset
    selected_symbol = st.selectbox("Asset", asset_symbols, index=asset_symbols.index('BTCUSD') if 'BTCUSD' in asset_symbols else 0)
    
    # Dapatkan data aset yang dipilih
    selected_asset = next((asset for asset in asset_data if asset['symbol'] == selected_symbol), None)
    
    if not selected_asset:
        st.error("Asset data not available")
        st.stop()
    
    # Tampilkan informasi dasar aset
    st.markdown(f"""
    <div class="card">
      <div class="flex items-center mb-4">
        <h3 class="text-lg font-bold">{selected_asset['symbol']}</h3>
        <span class="ml-2 px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
          {selected_asset['type'].capitalize()}
        </span>
      </div>
      
      <div class="grid grid-cols-2 gap-4">
        <div>
          <div class="metric-value">${selected_asset['current_price']:,.2f}</div>
          <div class="metric-label">Current Price</div>
        </div>
        
        <div>
          <div class="metric-value" style="color: {'#10b981' if selected_asset['price_change_percentage_24h'] >= 0 else '#ef4444'}">
            {selected_asset['price_change_percentage_24h']:.2f}%
          </div>
          <div class="metric-label">24h Change</div>
        </div>
      </div>
      
      <div class="mt-4 grid grid-cols-2 gap-2">
        <div>
          <div class="text-sm text-secondary">High</div>
          <div class="font-medium">${selected_asset['high_24h']:,.2f}</div>
        </div>
        
        <div>
          <div class="text-sm text-secondary">Low</div>
          <div class="font-medium">${selected_asset['low_24h']:,.2f}</div>
        </div>
        
        <div>
          <div class="text-sm text-secondary">Volume</div>
          <div class="font-medium">{selected_asset['volume']:,.0f}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# Tab utama
tab1, tab2, tab3 = st.tabs([
    "📊 Technical Analysis", 
    "📰 Market Sentiment", 
    "💡 Trading Recommendations"
])

with tab1:
    st.markdown(f'<h2 class="text-xl font-bold mb-4">Technical Analysis - {selected_asset["symbol"]}</h2>', unsafe_allow_html=True)
    
    # Kontrol analisis
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        days = st.slider("Time Range (days)", 30, 365, 90)
    with col2:
        show_indicators = st.checkbox("Show Technical Indicators", True)
    with col3:
        indicators = st.multiselect(
            "Select Indicators", 
            ["SMA", "EMA", "RSI", "MACD", "Bollinger Bands"],
            default=["SMA", "RSI"]
        )
    
    with st.spinner('Loading historical data...'):
        historical_df = backend.get_historical_data(selected_symbol, days)
    
    if historical_df.empty:
        st.warning(f"Historical data not available for {selected_symbol}")
    else:
        # Hitung indikator teknikal
        tech_df = backend.calculate_technical_indicators(historical_df)
        
        # Buat grafik interaktif dengan Plotly
        fig = make_subplots(
            rows=3 if ("RSI" in indicators and show_indicators) else 2 if ("MACD" in indicators and show_indicators) else 1, 
            cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.05,
            row_heights=[0.6, 0.2, 0.2] if ("RSI" in indicators and "MACD" in indicators and show_indicators) 
                         else [0.7, 0.3] if (("RSI" in indicators or "MACD" in indicators) and show_indicators)
                         else [1.0]
        )
        
        # Grafik harga utama
        fig.add_trace(go.Candlestick(
            x=tech_df['Date'],
            open=tech_df['Open'] if 'Open' in tech_df.columns else tech_df['price'],
            high=tech_df['High'] if 'High' in tech_df.columns else tech_df['price'],
            low=tech_df['Low'] if 'Low' in tech_df.columns else tech_df['price'],
            close=tech_df['price'],
            name='Price',
            increasing_line_color='#10b981',
            decreasing_line_color='#ef4444'
        ), row=1, col=1)
        
        # Tambahkan indikator yang dipilih
        row_counter = 1
        
        # Moving Averages
        if show_indicators and ("SMA" in indicators or "EMA" in indicators):
            if "SMA" in indicators:
                fig.add_trace(go.Scatter(
                    x=tech_df['Date'], 
                    y=tech_df['SMA_7'],
                    mode='lines',
                    name='SMA 7',
                    line=dict(color='#3b82f6', width=1.5)
                ), row=1, col=1)
                
                fig.add_trace(go.Scatter(
                    x=tech_df['Date'], 
                    y=tech_df['SMA_30'],
                    mode='lines',
                    name='SMA 30',
                    line=dict(color='#f59e0b', width=1.5)
                ), row=1, col=1)
            
            if "EMA" in indicators and 'EMA_12' in tech_df.columns:
                fig.add_trace(go.Scatter(
                    x=tech_df['Date'], 
                    y=tech_df['EMA_12'],
                    mode='lines',
                    name='EMA 12',
                    line=dict(color='#8b5cf6', width=1.5, dash='dot')
                ), row=1, col=1)
                
                fig.add_trace(go.Scatter(
                    x=tech_df['Date'], 
                    y=tech_df['EMA_26'],
                    mode='lines',
                    name='EMA 26',
                    line=dict(color='#ec4899', width=1.5, dash='dot')
                ), row=1, col=1)
        
        # Bollinger Bands
        if show_indicators and "Bollinger Bands" in indicators and 'BB_upper' in tech_df.columns:
            fig.add_trace(go.Scatter(
                x=tech_df['Date'],
                y=tech_df['BB_upper'],
                mode='lines',
                name='BB Upper',
                line=dict(color='#94a3b8', width=1)
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=tech_df['Date'],
                y=tech_df['BB_middle'],
                mode='lines',
                name='BB Middle',
                line=dict(color='#64748b', width=1.5)
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=tech_df['Date'],
                y=tech_df['BB_lower'],
                mode='lines',
                name='BB Lower',
                line=dict(color='#94a3b8', width=1),
                fill='tonexty',
                fillcolor='rgba(148, 163, 184, 0.1)'
            ), row=1, col=1)
        
        # RSI
        if show_indicators and "RSI" in indicators and 'RSI' in tech_df.columns:
            row_counter += 1
            fig.add_trace(go.Scatter(
                x=tech_df['Date'], 
                y=tech_df['RSI'],
                mode='lines',
                name='RSI',
                line=dict(color='#8b5cf6', width=1.5)
            ), row=row_counter, col=1)
            
            # Tambahkan area overbought dan oversold
            fig.add_hrect(y0=70, y1=100, line_width=0, fillcolor="red", opacity=0.1, row=row_counter, col=1)
            fig.add_hrect(y0=0, y1=30, line_width=0, fillcolor="green", opacity=0.1, row=row_counter, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=row_counter, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=row_counter, col=1)
            fig.add_hline(y=50, line_dash="dot", line_color="gray", row=row_counter, col=1)
        
        # MACD
        if show_indicators and "MACD" in indicators and 'MACD' in tech_df.columns:
            row_counter += 1
            fig.add_trace(go.Bar(
                x=tech_df['Date'], 
                y=tech_df['MACD_hist'],
                name='MACD Hist',
                marker_color=np.where(tech_df['MACD_hist'] < 0, '#ef4444', '#10b981')
            ), row=row_counter, col=1)
            
            fig.add_trace(go.Scatter(
                x=tech_df['Date'], 
                y=tech_df['MACD'],
                mode='lines',
                name='MACD',
                line=dict(color='#3b82f6', width=1.5)
            ), row=row_counter, col=1)
            
            fig.add_trace(go.Scatter(
                x=tech_df['Date'], 
                y=tech_df['MACD_signal'],
                mode='lines',
                name='Signal',
                line=dict(color='#f59e0b', width=1.5)
            ), row=row_counter, col=1)
            
            fig.add_hline(y=0, line_color="gray", row=row_counter, col=1)
        
        # Update layout
        fig.update_layout(
            height=700,
            title=f'{selected_asset["symbol"]} Technical Analysis',
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
        
        fig.update_xaxes(title_text="Date", row=row_counter, col=1)
        fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
        
        if "RSI" in indicators and show_indicators:
            fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0, 100])
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Interpretasi indikator
        if 'RSI' in tech_df and not tech_df['RSI'].isnull().all():
            current_rsi = tech_df['RSI'].iloc[-1]
            
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f'<h3 class="text-lg font-bold">Indicator Interpretation</h3>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                st.metric("Current RSI", f"{current_rsi:.1f}")
            
            with col2:
                st.metric("Status", 
                          "Overbought" if current_rsi > 70 else "Oversold" if current_rsi < 30 else "Neutral",
                          delta="Sell signal" if current_rsi > 70 else "Buy signal" if current_rsi < 30 else "No strong signal")
            
            with col3:
                if current_rsi > 70:
                    st.info("ℹ️ **Overbought Condition (RSI > 70)** - Price may be too high, potential downward correction.")
                elif current_rsi < 30:
                    st.info("ℹ️ **Oversold Condition (RSI < 30)** - Price may be too low, potential upward recovery.")
                else:
                    st.info("ℹ️ **RSI in Neutral Range (30-70)** - No strong signal from RSI indicator.")
            
            st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown(f'<h2 class="text-xl font-bold mb-4">Market Sentiment - {selected_asset["symbol"]}</h2>', unsafe_allow_html=True)
    
    if st.button("Load Latest Market News", type="primary", key="load_news"):
        with st.spinner('Fetching and analyzing market news...'):
            # Dapatkan berita
            news_items = backend.get_asset_news(selected_symbol)
            
            # Analisis sentimen
            sentiment_results = backend.analyze_news_sentiment(news_items, sentiment_model)
            
            if not sentiment_results:
                st.warning("No recent market news found")
            else:
                # Ringkasan sentimen
                positive_count = sum(1 for r in sentiment_results if r['sentiment'] == 'POSITIVE')
                negative_count = sum(1 for r in sentiment_results if r['sentiment'] == 'NEGATIVE')
                sentiment_score = positive_count / len(sentiment_results) if sentiment_results else 0
                
                # Visualisasi sentimen
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<h3 class="text-lg font-bold">Sentiment Summary</h3>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div class="flex flex-col items-center">
                      <div class="text-4xl font-bold" style="color: {'#10b981' if sentiment_score > 0.5 else '#ef4444'}">
                        {sentiment_score*100:.1f}%
                      </div>
                      <div class="text-secondary">Positive Sentiment Score</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col2:
                    st.markdown("""
                    <div class="flex flex-col">
                      <div class="flex justify-between mb-1">
                        <span>Positive</span>
                        <span>{positive_count}</span>
                      </div>
                      <div class="w-full bg-gray-200 rounded-full h-2.5">
                        <div class="bg-green-500 h-2.5 rounded-full" style="width: """ + f"{sentiment_score*100:.1f}" + """%"></div>
                      </div>
                      
                      <div class="flex justify-between mt-4 mb-1">
                        <span>Negative</span>
                        <span>{negative_count}</span>
                      </div>
                      <div class="w-full bg-gray-200 rounded-full h-2.5">
                        <div class="bg-red-500 h-2.5 rounded-full" style="width: """ + f"{(1-sentiment_score)*100:.1f}" + """%"></div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Tampilkan berita
                st.markdown('<h3 class="text-lg font-bold mt-6">Latest Market News</h3>', unsafe_allow_html=True)
                
                for result in sentiment_results:
                    sentiment_color = "#10b981" if result['sentiment'] == 'POSITIVE' else "#ef4444"
                    
                    with st.container():
                        st.markdown(f"""
                        <div class="card">
                          <div class="flex justify-between items-start mb-2">
                            <div class="flex items-center">
                              <div style="background: {sentiment_color}; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px;"></div>
                              <span style="color: {sentiment_color}; font-weight: 600;">{result['sentiment']}</span>
                            </div>
                            <span style="color: #64748b; font-size: 0.85rem;">{result.get('source', 'Unknown')}</span>
                          </div>
                          
                          <h4 class="font-semibold">{result['title']}</h4>
                          
                          <div class="mt-3 flex items-center text-sm text-secondary">
                            <span>{result.get('published_at', '')}</span>
                            <span class="mx-2">•</span>
                            <a href="{result['url']}" target="_blank" style="color: #2563eb; font-weight: 600;">
                              Read full article
                            </a>
                          </div>
                        </div>
                        """, unsafe_allow_html=True)

with tab3:
    st.markdown(f'<h2 class="text-xl font-bold mb-4">Trading Recommendations - {selected_asset["symbol"]}</h2>', unsafe_allow_html=True)
    
    if st.button("Generate Trading Analysis", type="primary", use_container_width=True):
        with st.spinner('Analyzing market data...'):
            # Dapatkan data historis
            historical_df = backend.get_historical_data(selected_symbol, 90)
            
            # Analisis teknikal
            if historical_df.empty:
                st.error("Historical data not available for analysis")
                st.stop()
                
            tech_df = backend.calculate_technical_indicators(historical_df)
            
            # Analisis sentimen
            news_items = backend.get_asset_news(selected_symbol)
            sentiment_results = backend.analyze_news_sentiment(news_items, sentiment_model)
            
            # Buat rekomendasi
            recommendation, confidence = backend.generate_trading_recommendation(
                selected_asset, tech_df, sentiment_results
            )
            
            # Tampilkan metrik dalam grid
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<h3 class="text-lg font-bold">Market Analysis</h3>', unsafe_allow_html=True)
            
            # Nilai indikator
            current_rsi = tech_df['RSI'].iloc[-1] if 'RSI' in tech_df.columns else 50
            positive_count = sum(1 for r in sentiment_results if r['sentiment'] == 'POSITIVE') if sentiment_results else 0
            total_count = len(sentiment_results) or 1
            sentiment_score = positive_count / total_count
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Price", f"${selected_asset['current_price']:,.2f}", 
                         f"{selected_asset['price_change_percentage_24h']:.2f}%")
            
            with col2:
                st.metric("RSI", f"{current_rsi:.1f}",
                         "Overbought" if current_rsi > 70 else "Oversold" if current_rsi < 30 else "Neutral")
            
            with col3:
                st.metric("Sentiment", f"{sentiment_score*100:.1f}%",
                         "Positive" if sentiment_score > 0.6 else "Negative" if sentiment_score < 0.4 else "Neutral")
            
            # Visualisasi faktor
            fig = go.Figure()
            
            # Tambahkan radar chart
            fig.add_trace(go.Scatterpolar(
                r=[current_rsi/100, sentiment_score, 0.8, 0.65],
                theta=['RSI', 'Sentiment', 'Volatility', 'Momentum'],
                fill='toself',
                name='Analysis Factors',
                line=dict(color='#2563eb')
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1]
                    )),
                showlegend=False,
                height=400,
                margin=dict(l=50, r=50, t=30, b=50),
                font=dict(family="Inter, sans-serif")
            )
            
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Rekomendasi trading
            st.markdown('<div class="card">', unsafe_allow_html=True)
            
            # Header rekomendasi
            if recommendation == "BELI":
                st.markdown('<div class="bg-green-50 border border-green-200 rounded-lg p-6">', unsafe_allow_html=True)
                st.markdown('<h3 class="text-2xl font-bold text-green-800 flex items-center">✅ BUY Recommendation</h3>', unsafe_allow_html=True)
                color_class = "text-green-600"
            elif recommendation == "JUAL":
                st.markdown('<div class="bg-red-50 border border-red-200 rounded-lg p-6">', unsafe_allow_html=True)
                st.markdown('<h3 class="text-2xl font-bold text-red-800 flex items-center">❌ SELL Recommendation</h3>', unsafe_allow_html=True)
                color_class = "text-red-600"
            else:
                st.markdown('<div class="bg-blue-50 border border-blue-200 rounded-lg p-6">', unsafe_allow_html=True)
                st.markdown('<h3 class="text-2xl font-bold text-blue-800 flex items-center">⏱️ HOLD Recommendation</h3>', unsafe_allow_html=True)
                color_class = "text-blue-600"
            
            st.markdown(f"""
            <div class="mt-4 flex items-center">
              <div class="text-4xl font-bold {color_class}">{confidence}%</div>
              <div class="ml-3">
                <div class="text-secondary">Confidence Level</div>
                <div class="w-48 bg-gray-200 rounded-full h-2.5 mt-1">
                  <div class="h-2.5 rounded-full" style="background-color: {color_class.replace('text-', '').replace('-600', '-500')}; width: {confidence}%"></div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Alasan rekomendasi
            st.markdown('<h4 class="text-lg font-bold mt-6">Analysis Summary</h4>', unsafe_allow_html=True)
            
            if recommendation == "BELI":
                st.markdown("""
                <ul class="list-disc pl-5 space-y-2 mt-3">
                  <li>Technical indicators suggest potential upward movement</li>
                  <li>Market sentiment is predominantly positive</li>
                  <li>Current price shows strong support levels</li>
                  <li>Volume patterns indicate increasing buying pressure</li>
                </ul>
                
                <div class="mt-4 p-4 bg-green-50 rounded-lg">
                  <h5 class="font-semibold text-green-800">Trading Strategy</h5>
                  <p class="mt-2">Consider entering a long position with stop-loss at recent support level. Take profit targets at key resistance levels.</p>
                </div>
                """, unsafe_allow_html=True)
                
            elif recommendation == "JUAL":
                st.markdown("""
                <ul class="list-disc pl-5 space-y-2 mt-3">
                  <li>Technical indicators suggest potential downward movement</li>
                  <li>Market sentiment is predominantly negative</li>
                  <li>Current price shows resistance at key levels</li>
                  <li>Volume patterns indicate increasing selling pressure</li>
                </ul>
                
                <div class="mt-4 p-4 bg-red-50 rounded-lg">
                  <h5 class="font-semibold text-red-800">Trading Strategy</h5>
                  <p class="mt-2">Consider entering a short position with stop-loss at recent resistance level. Take profit targets at key support levels.</p>
                </div>
                """, unsafe_allow_html=True)
                
            else:
                st.markdown("""
                <ul class="list-disc pl-5 space-y-2 mt-3">
                  <li>Technical indicators show mixed signals</li>
                  <li>Market sentiment is neutral with no clear direction</li>
                  <li>Price is consolidating within a range</li>
                  <li>Volume patterns show decreased participation</li>
                </ul>
                
                <div class="mt-4 p-4 bg-blue-50 rounded-lg">
                  <h5 class="font-semibold text-blue-800">Trading Strategy</h5>
                  <p class="mt-2">Monitor key support and resistance levels. Consider range-bound strategies or wait for clearer directional signals before entering new positions.</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer">
  <div class="flex justify-between items-center">
    <div>
      <strong>Quantum Analyst Pro</strong> | Advanced Trading Analytics
    </div>
    <div>
      Data Sources: Binance API • Yahoo Finance • CryptoPanic
    </div>
  </div>
  <div class="mt-2 text-center">
    Last updated: {}
  </div>
</div>
""".format(datetime.now().strftime('%d %B %Y %H:%M')), unsafe_allow_html=True)
