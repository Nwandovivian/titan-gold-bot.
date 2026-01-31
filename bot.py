import telebot
import requests
import pandas as pd
import numpy as np
import time
import os
import xml.etree.ElementTree as ET
from threading import Thread
from flask import Flask

# --- CLOUD ALIVE SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Titan is Awake"
def run_web(): app.run(host='0.0.0.0', port=8080)

# --- CONFIG ---
TOKEN = "7334133413:AAE1AfxFXYNvr1d3woN7jOJzqG-lYtw2HG8"
RECIPIENTS = ["6503404797", "5771190633", "-1003730879805"]
SYMBOL = "XAUTUSDT"

bot = telebot.TeleBot(TOKEN, threaded=True)
STATE = {"active_trade": None, "msg_ids": {}, "last_news": []}

def get_vitals():
    try:
        url = f"https://api.mexc.com/api/v3/klines?symbol={SYMBOL}&interval=15m&limit=50"
        data = requests.get(url, timeout=5).json()
        df = pd.DataFrame(data, columns=['ts','o','h','l','c','v','ct','qv']).astype(float)
        price = df['c'].iloc[-1]
        delta = df['c'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain / (loss + 1e-10)))).iloc[-1]
        return price, rsi
    except: return None, 50

def send_signal(chat_id=None):
    price, rsi = get_vitals()
    if not price: return
    
    side = "BUY" if rsi < 45 else "SELL"
    tp = round(price + (3.20 if side == "BUY" else -3.20), 2)
    sl = round(price - (2.10 if side == "BUY" else -2.10), 2)
    
    # --- MANDATORY REASONING ---
    if side == "BUY":
        reason = f"RSI is at {round(rsi,1)}, indicating Gold is oversold on the 15m chart. Expecting a bullish reversal."
    else:
        reason = f"RSI is at {round(rsi,1)}, signaling overbought conditions. High probability of a price drop/correction."
    
    msg = (f"🔱 <b>TITAN SIGNAL: {side} GOLD</b>\n"
           f"━━━━━━━━━━━━━━━━━━━━\n"
           f"💵 <b>ENTRY:</b> ${price}\n"
           f"🎯 <b>TP:</b> ${tp} | 🛡 <b>SL:</b> ${sl}\n\n"
           f"🧠 <b>REASON:</b> {reason}\n"
           f"📟 <i>Tracking Live Pips...</i>")
    
    STATE["active_trade"] = {"side": side, "entry": price, "tp": tp, "sl": sl, "reason": reason}
    
    targets = [chat_id] if chat_id else RECIPIENTS
    for rid in targets:
        try:
            m = bot.send_message(rid, msg, parse_mode="HTML")
            STATE["msg_ids"][rid] = m.message_id
        except: pass

@bot.message_handler(func=lambda m: True)
def handle_commands(m):
    if any(x in m.text.lower() for x in ["trade", "signal", "now"]):
        send_signal(m.chat.id)

def live_tracker():
    while True:
        if STATE["active_trade"]:
            curr_price, _ = get_vitals()
            if curr_price:
                trade = STATE["active_trade"]
                diff = (curr_price - trade['entry']) if trade['side'] == "BUY" else (trade['entry'] - curr_price)
                pips = round(diff / 0.01, 1)
                icon = "🟢" if pips >= 0 else "🔴"
                for rid, mid in STATE["msg_ids"].items():
                    try:
                        upd = (f"🔱 <b>LIVE TRACKER: {trade['side']}</b>\n"
                               f"━━━━━━━━━━━━━━━━━━━━\n"
                               f"💵 <b>Spot:</b> ${curr_price}\n"
                               f"📊 <b>P/L:</b> {icon} {pips} Pips\n"
                               f"🧠 <b>Reason:</b> {trade['reason']}")
                        bot.edit_message_text(upd, rid, mid, parse_mode="HTML")
                    except: pass
        time.sleep(20)

if __name__ == "__main__":
    Thread(target=run_web).start()
    Thread(target=live_tracker, daemon=True).start()
    bot.infinity_polling()
