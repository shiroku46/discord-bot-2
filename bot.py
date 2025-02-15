import discord
import openai
import asyncio
from discord.ext import commands

# OpenAI APIキー（環境変数から取得することを推奨）
openai.api_key = "your_openai_api_key"

# Botの設定
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 会話履歴の保存用（ユーザーごとに管理）
conversation_history = {}

# 会話履歴の保持時間（秒）
HISTORY_EXPIRATION = 300  # 5分間

async def manage_history(user_id):
    """一定時間後に会話履歴を削除"""
    await asyncio.sleep(HISTORY_EXPIRATION)
    if user_id in conversation_history:
        del conversation_history[user_id]

@bot.event
async def on_ready():
    print(f"ログインしました: {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Bot自身のメッセージは無視

    user_id = message.author.id
    user_name = message.author.name  # ユーザー名取得

    # 履歴がなければ初期化
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    # ユーザーの過去の発言を保存
    conversation_history[user_id].append({"role": "user", "content": message.content})

    # OpenAI API に送るメッセージリストを作成
    messages = [{"role": "system", "content": "あなたは『サイカワ』です。『桝見荘』の管理人代行をしています。"}]
    messages.extend(conversation_history[user_id])

    # OpenAI API を使用して返答を生成
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    reply = response["choices"][0]["message"]["content"]

    # 返答を履歴に保存
    conversation_history[user_id].append({"role": "assistant", "content": reply})

    # ユーザー名を呼びながら返信
    reply_with_name = f"{user_name}様、{reply}"
    await message.channel.send(reply_with_name)

    # 履歴管理タスクをスケジュール
    asyncio.create_task(manage_history(user_id))

# Botの実行
bot.run("your_discord_bot_token")
