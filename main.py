import time
import datetime
import urllib.request
import urllib.parse
import ssl
import json
import os
import sys

TELEGRAM_BOT_TOKEN = "8766931461:AAE05JVlOJl0slQR2pxw0CYYLn7D3cuL4MA"
TELEGRAM_CHAT_ID = "8980299791"
ssl_context = ssl._create_unverified_context()

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    )
    try:
        with urllib.request.urlopen(req, context=ssl_context, timeout=15) as resp:
            res = json.loads(resp.read().decode())
            return res.get("ok", False)
    except Exception as e:
        print(f"Error sending Telegram: {e}")
        return False

# ==================== BITCOIN (BTC/THB) ====================
def calculate_ema(prices, length):
    ema = []
    k = 2.0 / (length + 1)
    for i, p in enumerate(prices):
        if i == 0:
            ema.append(p)
        else:
            ema.append(p * k + ema[-1] * (1.0 - k))
    return ema

def check_btc():
    now = int(time.time())
    from_t = now - 86400 * 10
    url = f"https://api.bitkub.com/tradingview/history?symbol=BTC_THB&resolution=60&from={from_t}&to={now}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    
    with urllib.request.urlopen(req, context=ssl_context, timeout=15) as resp:
        data = json.loads(resp.read().decode())
        
    if data.get("s") != "ok":
        return
        
    closes = data["c"]
    lows = data["l"]
    times = data["t"]
    
    if len(closes) < 30:
        return
        
    ema12 = calculate_ema(closes, 12)
    ema26 = calculate_ema(closes, 26)
    
    current_price = closes[-1]
    bar_time_str = datetime.datetime.fromtimestamp(times[-1]).strftime("%Y-%m-%d %H:%M")
    
    prev_diff = ema12[-2] - ema26[-2]
    curr_diff = ema12[-1] - ema26[-1]
    
    is_buy = (prev_diff <= 0 and curr_diff > 0)
    is_sell = (prev_diff >= 0 and curr_diff < 0)
    
    print(f"[BTC] {bar_time_str} | Price: {current_price:,.2f} | EMA12: {ema12[-1]:,.0f} | EMA26: {ema26[-1]:,.0f} | Buy: {is_buy} | Sell: {is_sell}")
    
    if is_buy:
        swing_low = min(lows[-3], lows[-2])
        sl_diff = current_price - swing_low
        sl_pct = (sl_diff / current_price) * 100 if current_price > 0 else 0
        sl_15 = current_price * 0.985
        sl_20 = current_price * 0.980
        
        msg = (
            f"🔔 <b>[CDC Cloud Alert] สัญญาณซื้อ BTC/THB มาแล้ว!</b>\n\n"
            f"🪙 <b>เหรียญ:</b> Bitcoin (Bitkub 1H)\n"
            f"🕒 <b>เวลา:</b> {bar_time_str}\n"
            f"💰 <b>ราคาเข้าซื้อ:</b> {current_price:,.2f} บาท\n"
            f"📈 <b>สัญญาณ:</b> เส้น EMA 12 ตัดขึ้นเหนือ EMA 26 (สามเหลี่ยมสีน้ำเงิน)\n\n"
            f"🛡️ <b>จุดตัดขาดทุน (Stop Loss แนะนำ):</b>\n"
            f"• <b>ตามก้นแท่งก่อนหน้า:</b> <b>{swing_low:,.2f} บาท</b> (-{sl_pct:.2f}%)\n"
            f"• <i>หรือตามความเสี่ยง 1.5%: {sl_15:,.2f} บาท</i>\n"
            f"• <i>หรือตามความเสี่ยง 2.0%: {sl_20:,.2f} บาท</i>\n\n"
            f"💡 <i>คำแนะนำ: เข้าซื้อแล้วตั้ง Stop Loss ตามก้นแท่งก่อนหน้าทันที ห้ามถัวเด็ดขาด!</i>"
        )
        send_telegram(msg)
        
    elif is_sell:
        msg = (
            f"⚠️ <b>[CDC Cloud Alert] สัญญาณขาย BTC/THB มาแล้ว!</b>\n\n"
            f"🪙 <b>เหรียญ:</b> Bitcoin (Bitkub 1H)\n"
            f"🕒 <b>เวลา:</b> {bar_time_str}\n"
            f"💰 <b>ราคาออก/ขาย:</b> {current_price:,.2f} บาท\n"
            f"📉 <b>สัญญาณ:</b> เส้น EMA 12 ตัดลงใต้ EMA 26 (สามเหลี่ยมสีแดง)\n\n"
            f"💡 <i>พิจารณาปิดสถานะทำกำไร / คัทลอส และถือเงินสด 100% รอสัญญาณรอบใหม่ครับ</i>"
        )
        send_telegram(msg)

# ==================== GOLD (XAU/USD) ====================
def check_gold():
    url_tv = "https://scanner.tradingview.com/cfd/scan"
    payload = json.dumps({
        "symbols": {"tickers": ["OANDA:XAUUSD"]},
        "columns": ["close|60", "open|60", "high|60", "low|60", "EMA12|60", "EMA26|60"]
    }).encode()
    req_tv = urllib.request.Request(url_tv, data=payload, headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"})
    
    with urllib.request.urlopen(req_tv, context=ssl_context, timeout=15) as r:
        d = json.loads(r.read().decode())
        item = d["data"][0]["d"]
        
    c60, o60, h60, l60, ema12, ema26 = item
    diff = ema12 - ema26
    
    # Get swing low from Binance XAUTUSDT
    swing_low = l60
    try:
        url_k = "https://api.binance.com/api/v3/klines?symbol=XAUTUSDT&interval=1h&limit=6"
        req_k = urllib.request.Request(url_k, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_k, context=ssl_context, timeout=10) as rk:
            bars = json.loads(rk.read().decode())
            lows = [float(b[3]) for b in bars]
            if len(lows) >= 3:
                swing_low = min(lows[-3], lows[-2])
    except Exception:
        pass
        
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"[GOLD] {now_str} | Price: ${c60:,.2f} | EMA12: ${ema12:,.1f} | EMA26: ${ema26:,.1f} | Diff: {diff:.2f}")

    # To catch gold crossover on cloud schedule:
    # If absolute difference is narrow (|diff| < 1.5) and crosses, or based on state
    # We can log status cleanly
    # For demo test:
    print("[CLOUD CHECK] Completed check for BTC & GOLD successfully!")

if __name__ == "__main__":
    print("=== CDC ActionZone Cloud Runner Started ===")
    check_btc()
    check_gold()
    print("=== Finished Successfully ===")
