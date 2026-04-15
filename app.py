import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
import plotly.graph_objects as go

# Uygulama Ayarları
st.set_page_config(page_title="Silver Quant Terminal", layout="wide")
st.title("🪙 Gümüş (XAG/TRY) Analiz Terminali")

# 1. VERİ ÇEKME VE HESAPLAMA (Gümüş Ons + Dolar Kuru)
@st.cache_data(ttl=300) # 5 dakikada bir verileri tazeler
def get_market_data():
    # SI=F (Gümüş Ons), USDTRY=X (Dolar/TL)
    data = yf.download(["SI=F", "USDTRY=X"], period="6mo", interval="1d")
    
    # Çoklu indeksi temizle ve sadece Kapanış (Close) fiyatlarını al
    df_silver = data['Close']['SI=F'].to_frame(name='Silver_Ons')
    df_usdtry = data['Close']['USDTRY=X'].to_frame(name='USDTRY')
    
    # Verileri birleştir
    df = pd.concat([df_silver, df_usdtry], axis=1).ffill()
    
    # GRAM TL HESABI: (Ons Fiyatı / 31.1035) * Dolar Kuru
    df['Gram_TL'] = (df['Silver_Ons'] / 31.1035) * df['USDTRY']
    
    # TEKNİK ANALİZ (Gram TL Üzerinden)
    # RSI
    delta = df['Gram_TL'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df['Gram_TL'].ewm(span=12, adjust=False).mean()
    exp2 = df['Gram_TL'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # Bollinger Bantları
    df['MA20'] = df['Gram_TL'].rolling(window=20).mean()
    df['STD20'] = df['Gram_TL'].rolling(window=20).std()
    df['BB_Upper'] = df['MA20'] + (df['STD20'] * 2)
    df['BB_Lower'] = df['MA20'] - (df['STD20'] * 2)
    
    return df

try:
    df = get_market_data()
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    # METRİKLER (Gram TL ve Ons USD)
    col1, col2, col3 = st.columns(3)
    col1.metric("Gümüş Gram (TL)", f"{latest['Gram_TL']:.2f} ₺", f"{latest['Gram_TL'] - prev['Gram_TL']:.2f} ₺")
    col2.metric("Gümüş Ons (USD)", f"${latest['Silver_Ons']:.2f}", f"${latest['Silver_Ons'] - prev['Silver_Ons']:.2f}")
    col3.metric("USD/TRY Kuru", f"{latest['USDTRY']:.2f} ₺")

    st.divider()

    # 2. AL/SAT SİNYAL ÜRETİCİ (Hata düzeltildi)
    st.subheader("📊 Algoritmik Sinyaller (Gram/TL Bazlı)")
    
    rsi = latest['RSI']
    macd = latest['MACD']
    macd_signal = latest['MACD_Signal']
    price = latest['Gram_TL']
    bb_lower = latest['BB_Lower']
    bb_upper = latest['BB_Upper']

    signal = "NÖTR 🟡"
    reason = "Matematiksel göstergeler şu an dengede."

    if rsi < 30 and price <= bb_lower:
        signal = "GÜÇLÜ AL 🟢"
        reason = "RSI aşırı satımda ve fiyat alt Bollinger bandında. Wall Street tekniklerine göre tepki alımı beklenir."
    elif rsi > 70 and price >= bb_upper:
        signal = "GÜÇLÜ SAT 🔴"
        reason = "RSI aşırı alımda ve fiyat üst Bollinger bandında. Teknik olarak düzeltme kapıda."
    elif macd > macd_signal:
        signal = "AL 📈"
        reason = "MACD sinyal çizgisini yukarı kesti. Pozitif momentum devam ediyor."
    elif macd < macd_signal:
        signal = "SAT 📉"
        reason = "MACD sinyal çizgisini aşağı kesti. Negatif eğilim hakim."

    st.info(f"**ÖNERİ:** {signal}\n\n**GEREKÇE:** {reason}")

    # 3. GRAFİK
    st.subheader("📈 Gümüş Gram/TL Teknik Grafik")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Gram_TL'], name='Gram TL Fiyatı'))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], name='Üst Bant', line=dict(dash='dash', color='rgba(200,200,200,0.5)')))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], name='Alt Bant', line=dict(dash='dash', color='rgba(200,200,200,0.5)')))
    fig.update_layout(height=500, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Veri çekilirken bir hata oluştu: {e}")

# 4. GLOBAL HABERLER
st.divider()
st.subheader("🌍 Canlı Global Haber Akışı")
feed = feedparser.parse("https://news.google.com/rss/search?q=silver+market+news&hl=en-US&gl=US&ceid=US:en")
for entry in feed.entries[:5]:
    st.markdown(f"🔹 **[{entry.title}]({entry.link})**")
    st.caption(f"Yayınlanma: {entry.published}")
    
