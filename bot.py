import os
import discord
import openai
from discord.ext import commands
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI APIのセットアップ（新しいクライアントを使用）
client_openai = openai.OpenAI(api_key=OPENAI_API_KEY)

# Discord Botのセットアップ
intents = discord.Intents.default()
intents.message_content = True  # メッセージの内容を取得できるようにする
bot = commands.Bot(command_prefix="!", intents=intents)

# Botが起動したときの処理
@bot.event
async def on_ready():
    print(f"ログインしました: {bot.user}")

# メッセージを受け取ったときの処理
@bot.event
async def on_message(message):
    # Bot自身のメッセージは無視する
    if message.author == bot.user:
        return

    # OpenAI にメッセージを送信
    response = client_openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "あなたはキャラクターのロールプレイをするAIです。"},
            {"role": "user", "content": message.content}
        ]
    )

    reply = response.choices[0].message.content  # 最新の API に対応

    # 返信を送信
    await message.channel.send(reply)

# Botを起動
bot.run(DISCORD_TOKEN)
