import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import feedparser
import plotly.graph_objects as go

# Uygulama Ayarları (Mobil uyumlu geniş görünüm)
st.set_page_config(page_title="Silver Quant Terminal", layout="wide")
st.title("🪙 Gümüş (XAG/USD) Quant Analiz Terminali")
st.markdown("Matematiksel teknik analiz ve global haber akışı ile karar destek sistemi.")

# 1. VERİ ÇEKME (Gümüş Vadelileri: SI=F)
@st.cache_data(ttl=900) # Veriyi 15 dakikada bir günceller
def get_silver_data():
    silver = yf.Ticker("SI=F")
    df = silver.history(period="6mo") # Son 6 aylık veri
    
    # Teknik İndikatörleri Hesapla (Wall Street Standartları)
    df.ta.rsi(length=14, append=True) # Göreceli Güç Endeksi
    df.ta.macd(fast=12, slow=26, signal=9, append=True) # MACD
    df.ta.bbands(length=20, std=2, append=True) # Bollinger Bantları
    
    return df

df = get_silver_data()
current_price = df['Close'].iloc[-1]
prev_price = df['Close'].iloc[-2]
price_change = current_price - prev_price

st.metric(label="Güncel Gümüş Fiyatı (USD/ons)", 
          value=f"${current_price:.2f}", 
          delta=f"${price_change:.2f}")

st.divider()

# 2. MATEMATİKSEL AL/SAT SİNYALİ ÜRETİCİ
st.subheader("📊 Algoritmik Sinyaller (Günlük Periyot)")

# Son günün verilerini al
latest = df.iloc[-1]
rsi = latest['RSI_14']
macd = latest['MACD_12_26_9']
macd_signal = latest['MACDs_12_26_9']
close_price = latest['Close']
bb_lower = latest['BBL_20_2.0']
bb_upper = latest['BBU_20_2.0']

signal = "NÖTR 🟡"
reason = "Piyasa şu an yatay seyrediyor, net bir aşırı alım veya satım yok."

# Temel Quant Mantığı
if rsi < 30 and close_price <= bb_lower:
    signal = "GÜÇLÜ AL 🟢"
    reason = f"RSI çok düşük ({rsi:.1f}) ve fiyat alt Bollinger bandına ({bb_lower:.2f}) dokundu. Matematiksel olarak aşırı satım var (Tepki yükselişi beklenir)."
elif rsi > 70 and close_price >= bb_upper:
    signal = "GÜÇLÜ SAT 🔴"
    reason = f"RSI çok yüksek ({rsi:.1f}) ve fiyat üst Bollinger bandına ({bb_upper:.2f}) dokundu. Matematiksel olarak aşırı alım var (Düzeltme beklenir)."
elif macd > macd_signal and rsi > 50:
    signal = "AL 🟢 (Momentum)"
    reason = "MACD sinyal çizgisini yukarı kesti ve momentum pozitif."
elif macd < macd_signal and rsi < 50:
    signal = "SAT 🔴 (Momentum)"
    reason = "MACD sinyal çizgisini aşağı kesti ve momentum negatif."

st.info(f"**SİNYAL:** {signal}\n\n**Gerekçe:** {reason}")

# 3. PROFESYONEL GRAFİK ÇİZİMİ
fig = go.Figure(data=[go.Candlestick(x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'], name="Fiyat")])

fig.update_layout(title="Gümüş Mum Grafiği (Son 6 Ay)", xaxis_title="Tarih", yaxis_title="Fiyat (USD)", height=400)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# 4. GLOBAL HABER TARAMA (RSS üzerinden otomatik çekim)
st.subheader("🌍 Canlı Global Gümüş Haberleri")

@st.cache_data(ttl=1800) # Haberleri 30 dakikada bir günceller
def get_silver_news():
    # Google News RSS (İngilizce global haberler için)
    url = "https://news.google.com/rss/search?q=silver+market+or+silver+price&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    return feed.entries[:5] # En güncel 5 haber

news_entries = get_silver_news()

for entry in news_entries:
    with st.container():
        st.markdown(f"**[{entry.title}]({entry.link})**")
        st.caption(entry.published)
  
