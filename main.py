import os
import json
import requests
import websocket
import pandas as pd
from datetime import datetime
import discord
import asyncio
import threading

# 디스코드 봇 설정
TOKEN = os.getenv("BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# 디스코드 알림 함수
async def send_discord_alert(message):
    await client.wait_until_ready()
    user = await client.fetch_user(USER_ID)
    if user:
        await user.send(message)

def start_discord_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(client.start(TOKEN))

# WebSocket 콜백
def on_message(ws, message):
    data = json.loads(message)
    code = data['code']
    price = data['trade_price']
    volume = data['trade_volume']
    value = price * volume
    direction = data['ask_bid']  # 'BID' or 'ASK'

    if value >= 100000000:  # 고래 기준
        time_str = datetime.fromtimestamp(data['timestamp'] / 1000).strftime("%Y-%m-%d %H:%M:%S")
        msg = f"🐋 고래 감지!\n[{time_str}]\n종목: {code}\n가격: {price}원\n수량: {volume:.4f}\n금액: {value:,.0f}원\n방향: {'매수' if direction == 'BID' else '매도'}"
        print(msg)
        asyncio.run(send_discord_alert(msg))

def on_error(ws, error):
    print("🚨 오류:", error)

def on_close(ws, close_status_code, close_msg):
    print("❎ 연결 종료:", close_status_code, close_msg)

def on_open(ws):
    print("🚀 WebSocket 연결 성공")

def run_websocket():
    url = "wss://api.upbit.com/websocket/v1"
    payload = [
        {"ticket": "test"},
        {"type": "trade", "codes": get_top_30_coins(), "isOnlyRealtime": True}
    ]
    ws = websocket.WebSocketApp(url,
                                 on_message=on_message,
                                 on_error=on_error,
                                 on_close=on_close,
                                 on_open=on_open)
    ws.run_forever(ping_interval=60, sslopt={"cert_reqs": 0})

def get_top_30_coins():
    url = "https://api.upbit.com/v1/ticker"
    markets = requests.get("https://api.upbit.com/v1/market/all?isDetails=false").json()
    krw_markets = [m['market'] for m in markets if m['market'].startswith("KRW-")]
    result = requests.get(url, params={"markets": ",".join(krw_markets)}).json()
    sorted_markets = sorted(result, key=lambda x: x['acc_trade_price_24h'], reverse=True)[:30]
    return [m['market'] for m in sorted_markets]

if __name__ == "__main__":
    # 디스코드 봇 스레드 시작
    discord_thread = threading.Thread(target=start_discord_bot)
    discord_thread.start()

    # WebSocket 실행
    run_websocket()
