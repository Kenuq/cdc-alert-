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

# ==================== BITCOIN (BTC/THB) 1D ====================
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
    from_t = now - 86400 * 60
    url = f"https://api.bitkub.com/tradingview/history?symbol=BTC_THB&resolution=D&from={from_t}&to={now}"
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
    bar_date_str = datetime.datetime.fromtimestamp(times[-1]).strftime("%Y-%m-%d")
    
    prev_diff = ema12[-2] - ema26[-2]
    curr_diff = ema12[-1] - ema26[-1]
    
    is_buy = (prev_diff <= 0 and curr_diff > 0)
    is_sell = (prev_diff >= 0 and curr_diff < 0)
    
    print(f"[BTC 1D] {bar_date_str} | Price: {current_price:,.2f} | EMA12: {ema12[-1]:,.0f} | EMA26: {ema26[-1]:,.0f} | Buy: {is_buy} | Sell: {is_sell}")
    
    if is_buy:
        swing_low = min(lows[-3], lows[-2])
        sl_diff = current_price - swing_low
        sl_pct = (sl_diff / current_price) * 100 if current_price > 0 else 0
        sl_30 = current_price * 0.970
        sl_50 = current_price * 0.950
        
        msg = (
            f"🔔 <b>[CDC Cloud Alert] สัญญาณซื้อใหญ่ BTC/THB มาแล้ว!</b>\n\n"
            f"🪙 <b>เหรียญ:</b> Bitcoin (Bitkub รายวัน 1D)\n"
            f"📅 <b>รอบวันที่:</b> {bar_date_str}\n"
            f"💰 <b>ราคาเข้าซื้อ:</b> {current_price:,.2f} บาท\n"
            f"📈 <b>สัญญาณ:</b> เส้น EMA 12 ตัดขึ้นเหนือ EMA 26 ในกราฟ Day (สามเหลี่ยมสีน้ำเงิน)\n\n"
            f"🛡️ <b>จุดตัดขาดทุน (Stop Loss แนะนำ):</b>\n"
            f"• <b>ตามก้นแท่งวันก่อนหน้า:</b> <b>{swing_low:,.2f} บาท</b> (-{sl_pct:.2f}%)\n"
            f"• <i>หรือตามความเสี่ยง 3.0%: {sl_30:,.2f} บาท</i>\n"
            f"• <i>หรือตามความเสี่ยง 5.0%: {sl_50:,.2f} บาท</i>\n\n"
            f"💡 <i>คำแนะนำ: สัญญาณ Day เป็นเทรนด์ใหญ่ที่ทรงพลัง เข้าซื้อแล้วตั้ง Stop Loss ถือรันเทรนด์ยาวๆ ได้เลยครับ</i>"
        )
        send_telegram(msg)
        
    elif is_sell:
        msg = (
            f"⚠️ <b>[CDC Cloud Alert] สัญญาณขายใหญ่ BTC/THB มาแล้ว!</b>\n\n"
            f"🪙 <b>เหรียญ:</b> Bitcoin (Bitkub รายวัน 1D)\n"
            f"📅 <b>รอบวันที่:</b> {bar_date_str}\n"
            f"💰 <b>ราคาออก/ขาย:</b> {current_price:,.2f} บาท\n"
            f"📉 <b>สัญญาณ:</b> เส้น EMA 12 ตัดลงใต้ EMA 26 ในกราฟ Day (สามเหลี่ยมสีแดง)\n\n"
            f"💡 <i>พิจารณาขายทำกำไร / คัทลอส และเปลี่ยนมาถือเงินสด 100% เพื่อหลบขาลงรอบใหญ่ครับ</i>"
        )
        send_telegram(msg)

# ==================== GOLD (XAU/USD) 1D ====================
def check_gold():
    url_tv = "https://scanner.tradingview.com/cfd/scan"
    payload = json.dumps({
        "symbols": {"tickers": ["OANDA:XAUUSD"]},
        "columns": ["close", "open", "high", "low", "EMA12", "EMA26"]
    }).encode()
    req_tv = urllib.request.Request(url_tv, data=payload, headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"})
    
    with urllib.request.urlopen(req_tv, context=ssl_context, timeout=15) as r:
        d = json.loads(r.read().decode())
        item = d["data"][0]["d"]
        
    c, o, h, l, ema12, ema26 = item
    diff = ema12 - ema26
    
    swing_low = l
    try:
        url_k = "https://api.binance.com/api/v3/klines?symbol=XAUTUSDT&interval=1d&limit=6"
        req_k = urllib.request.Request(url_k, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_k, context=ssl_context, timeout=10) as rk:
            bars = json.loads(rk.read().decode())
            lows = [float(b[3]) for b in bars]
            if len(lows) >= 3:
                swing_low = min(lows[-3], lows[-2])
    except Exception:
        pass
        
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"[GOLD 1D] {now_str} | Price: ${c:,.2f} | EMA12: ${ema12:,.1f} | EMA26: ${ema26:,.1f} | Diff: {diff:.2f}")

    if abs(diff) < 3.0 and diff > 0:
        sl_diff = c - swing_low
        sl_pct = (sl_diff / c) * 100 if c > 0 else 0
        msg = (
            f"🔔 <b>[CDC Cloud Alert] สัญญาณซื้อใหญ่ ทองคำ (XAU/USD 1D) มาแล้ว!</b>\n\n"
            f"🥇 <b>สินทรัพย์:</b> ทองคำ Gold Spot (รายวัน 1D)\n"
            f"🕒 <b>เวลา:</b> {now_str}\n"
            f"💰 <b>ราคาเข้าซื้อ:</b> ${c:,.2f} USD\n"
            f"📈 <b>สัญญาณ:</b> เส้น EMA 12 ตัดขึ้นเหนือ EMA 26 ในกราฟ Day (สามเหลี่ยมสีน้ำเงิน)\n\n"
            f"🛡️ <b>จุดตัดขาดทุน (Stop Loss แนะนำ):</b>\n"
            f"• <b>ตามก้นแท่งวันก่อนหน้า:</b> <b>${swing_low:,.2f} USD</b> (-{sl_pct:.2f}%)\n"
            f"• <i>หรือตามความเสี่ยง 1.5%: ${c*0.985:,.2f} USD</i>\n"
            f"• <i>หรือตามความเสี่ยง 2.0%: ${c*0.980:,.2f} USD</i>\n\n"
            f"💡 <i>คำแนะนำ: สัญญาณ Day เป็นเทรนด์ใหญ่ เข้าซื้อแล้วตั้ง Stop Loss ถือรันเทรนด์ยาวๆ ได้เลยครับ</i>"
        )
        send_telegram(msg)

if __name__ == "__main__":
    print("=== CDC ActionZone 1D Cloud Check Started ===")
    check_btc()
    check_gold()
    print("=== 1D Cloud Check Finished Successfully ===")
