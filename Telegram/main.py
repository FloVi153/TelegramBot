
import os
import time
import requests
import yfinance as yf
import pandas as pd
import numpy as np

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_signal(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

def get_data(symbol="^IXIC", interval="1h", period="2d"):
    data = yf.download(tickers=symbol, interval=interval, period=period)
    return data

def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def detect_chart_signal():
    data = get_data()
    if data is None or len(data) < 20:
        return None

    data['RSI'] = calculate_rsi(data)
    data['Trend'] = data['Close'].diff().rolling(window=3).mean()

    latest = data.iloc[-1]
    price = round(latest['Close'], 2)
    rsi = latest['RSI']
    trend = latest['Trend']

    if rsi < 30 and trend > 0:
        return f"📊 <b>Signal: NASDAQ</b>\n🟢 <b>LONG empfohlen</b>\nEinstieg: {price}\nSL: {round(price * 0.985, 2)}\nTP: {round(price * 1.02, 2)}\n🔁 Plattform: Trading212"
    elif rsi > 70 and trend < 0:
        return f"📊 <b>Signal: NASDAQ</b>\n🔴 <b>SHORT empfohlen</b>\nEinstieg: {price}\nSL: {round(price * 1.015, 2)}\nTP: {round(price * 0.97, 2)}\n🔁 Plattform: Trade Republic"
    return None

last_signal = ""
while True:
    try:
        signal = detect_chart_signal()
        if signal and signal != last_signal:
            send_signal(signal)
            last_signal = signal
    except Exception as e:
        print(f"Fehler: {e}")
    time.sleep(300)  # alle 5 Minuten prüfen
