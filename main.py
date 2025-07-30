import discord
import os

TOKEN = os.getenv("BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    user = await client.fetch_user(USER_ID)
    await user.send("📢 WhaleSignalBot 정상 작동 중입니다.")
    await client.close()

client.run(TOKEN)
