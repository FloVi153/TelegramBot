# Finaler Bot-Code mit Live-Trading-Signalen, /test, /ausblick, Abend-Scan
# Anforderungen: Python 3.10+, "python-telegram-bot", "yfinance", "schedule", "pandas"

import logging
import yfinance as yf
import datetime
import pandas as pd
import schedule
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === CONFIG ===
TOKEN = "7875344663:AAGj8IRtHVZtzI1KFwfNcBHfbG5YTy15pcs"
CHAT_ID = "1374880672"
ASSETS = ["BTC-USD", "ETH-USD", "^NDX", "^GSPC", "GC=F", "AAPL", "TSLA", "PLTR"]

# === LOGGING ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# === STRATEGIE ===
def check_signals():
    messages = []
    for symbol in ASSETS:
        data = yf.download(symbol, period="5d", interval="30m")
        if len(data) < 14:
            continue

        rsi = compute_rsi(data["Close"], 14)
        last_close = data["Close"].iloc[-1]
        volume_spike = data["Volume"].iloc[-1] > data["Volume"].rolling(10).mean().iloc[-1] * 2

        # Candle-Erkennung
        candles = data.iloc[-2:]
        candle_pattern = ""
        if candles["Close"].iloc[-1] > candles["Open"].iloc[-1] and candles["Open"].iloc[-1] < candles["Close"].iloc[-2]:
            candle_pattern = "Bullish Engulfing"

        if rsi < 30 or candle_pattern or volume_spike:
            msg = f"\n📊 Signal: {symbol}\n"
            msg += f"📈 Kurs: {last_close:.2f}\n"
            msg += f"📉 RSI: {rsi:.2f}\n"
            if candle_pattern:
                msg += f"🕯️ Pattern: {candle_pattern}\n"
            if volume_spike:
                msg += "🔥 Volumenanstieg erkannt\n"
            msg += f"🔁 Plattform: Trade Republic oder Trading 212\n"
            messages.append(msg)
    return messages

# === RSI BERECHNUNG ===
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

# === HANDLER ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Willkommen! Nutze /test oder /ausblick für Signale.")

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 TESTSIGNAL: Palantir (PLTR)\n🟢 LONG empfohlen\nEinstieg: 19,40 $ | TP: 21,00 $ | SL: 18,60 $\n(Kein echtes Signal – Funktionstest)"
    )

async def ausblick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messages = check_signals()
    if messages:
        for msg in messages:
            await context.bot.send_message(chat_id=CHAT_ID, text=msg)
    else:
        await context.bot.send_message(chat_id=CHAT_ID, text="📭 Keine guten Chancen gefunden.")

# === TÄGLICHER ABEND-SCAN ===
def abend_scan():
    app = ApplicationBuilder().token(TOKEN).build()
    messages = check_signals()
    for msg in messages:
        app.bot.send_message(chat_id=CHAT_ID, text=msg)

# === BOT STARTEN ===
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("test", test))
app.add_handler(CommandHandler("ausblick", ausblick))

# === GEPLANTER ABEND-SCAN ===
schedule.every().day.at("20:00").do(abend_scan)

async def main_loop():
    while True:
        schedule.run_pending()
        await asyncio.sleep(30)

if __name__ == '__main__':
    import asyncio
    app.run_polling()
    asyncio.run(main_loop())

