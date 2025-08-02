import os
import json
import requests
import websocket
from datetime import datetime
import asyncio
import discord

TOKEN = os.getenv("BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

async def send_discord_alert(message):
    await client.wait_until_ready()
    user = await client.fetch_user(USER_ID)
    if user:
        try:
            await user.send(message)
        except Exception as e:
            print(f"❌ DM 전송 실패: {e}")
    else:
        print("❌ USER_ID로 유저를 찾지 못했습니다.")

def send_alert_sync(msg):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_send_alert_and_quit(msg, loop))

async def _send_alert_and_quit(message, loop):
    try:
        await client.login(TOKEN)
        await client.connect()
        await send_discord_alert(message)
    finally:
        await client.close()
        loop.stop()

def on_message(ws, message):
    data = json.loads(message)
    code = data['code']
    price = data['trade_price']
    volume = data['trade_volume']
    value = price * volume
    direction = data['ask_bid']
    if value >= 100_000_000:
        time_str = datetime.fromtimestamp(data['timestamp'] / 1000).strftime("%Y-%m-%d %H:%M:%S")
        msg = f"""🐋 고래 감지!
[시간]: {time_str}
[종목]: {code}
[가격]: {price:,.0f}원
[수량]: {volume:.4f}
[금액]: {value:,.0f}원
[방향]: {'매수' if direction == 'BID' else '매도'}"""
        print(msg)
        send_alert_sync(msg)

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
    try:
        run_websocket()  # 이 안에서 조건 만족하면 메시지를 보냄
    except KeyboardInterrupt:
        print("⛔ 종료 요청됨")
