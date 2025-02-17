import discord
import openai
import asyncio
import os
import random
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# .env ファイルの読み込み
load_dotenv()

# APIキーの取得
openai.api_key = os.getenv("OPENAI_API_KEY")
discord_token = os.getenv("DISCORD_TOKEN")

if not openai.api_key:
    print("❌ エラー: OPENAI_API_KEY が設定されていません。環境変数を確認してください。")
    exit(1)

if not discord_token:
    print("❌ エラー: DISCORD_TOKEN が設定されていません。環境変数を確認してください。")
    exit(1)

# Botの設定
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 会話履歴の保存用
conversation_history = {}
character_settings = {}
HISTORY_EXPIRATION = 300

async def manage_history(user_id):
    await asyncio.sleep(HISTORY_EXPIRATION)
    if user_id in conversation_history:
        del conversation_history[user_id]

@bot.event
async def on_ready():
    try:
        if not hasattr(bot, "synced"):
            await bot.tree.sync()
            bot.synced = True
        print(f"✅ ログインしました: {bot.user}")
    except discord.HTTPException as e:
        print(f"⚠ コマンド同期失敗: {e}")

@bot.tree.command(name="set_character", description="キャラクター設定を追加")
async def set_character(interaction: discord.Interaction, setting: str):
    guild_id = interaction.guild.id
    if guild_id not in character_settings:
        character_settings[guild_id] = []
    character_settings[guild_id].append(setting)
    await interaction.response.send_message(f"キャラクター設定を追加しました: {setting}")

@bot.tree.command(name="list_character", description="キャラクター設定の一覧を表示")
async def list_character(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    settings = character_settings.get(guild_id, ["デフォルト設定: 『仁井垣巳乙』です。『桝見荘』の管理人をしています。"])
    await interaction.response.send_message("現在のキャラクター設定:\n" + "\n".join(settings))

@bot.tree.command(name="reset_character", description="キャラクター設定をリセット")
async def reset_character(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    character_settings[guild_id] = []
    await interaction.response.send_message("キャラクター設定をリセットしました。")

@bot.tree.command(name="upload_character", description="キャラクター設定を.txtファイルから上書き")
async def upload_character(interaction: discord.Interaction, file: discord.Attachment):
    guild_id = interaction.guild.id
    if not file.filename.endswith(".txt"):
        await interaction.response.send_message("❌ エラー: .txt ファイルをアップロードしてください。")
        return
    
    content = await file.read()
    character_settings[guild_id] = content.decode("utf-8").splitlines()
    await interaction.response.send_message("✅ キャラクター設定を更新しました。")

@bot.tree.command(name="help", description="利用可能なコマンドの一覧を表示")
async def help_command(interaction: discord.Interaction):
    help_text = (
        "利用可能なコマンド一覧:\n"
        "/set_character [設定] - キャラクター設定を追加\n"
        "/list_character - キャラクター設定の一覧を表示\n"
        "/reset_character - キャラクター設定をリセット\n"
        "/upload_character [ファイル] - .txtファイルからキャラクター設定を更新\n"
    )
    await interaction.response.send_message(help_text)

@bot.event
async def on_message(message):
    if message.author.bot:
        return  
    if bot.user not in message.mentions:
        return  
    user_id = message.author.id
    user_name = f"{message.author.display_name}"
    guild_id = message.guild.id if message.guild else None
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    conversation_history[user_id].append({"role": "user", "content": message.content})
    system_messages = character_settings.get(guild_id, ["あなたは『仁井垣巳乙』です。『桝見荘』の管理人をしています。あなたは今後、仁井垣巳乙という幼い人物としてロールプレイをしつつ、フランクな口調で話をしてください。"])
    messages = [{"role": "system", "content": setting} for setting in system_messages]
    messages.extend(conversation_history[user_id])
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        reply = response.choices[0].message.content.replace("**", "")  # 太字の解除
        conversation_history[user_id].append({"role": "assistant", "content": reply})
        patterns = [
            f"{user_name}、{reply}",  # 最初にユーザー名
            f"{reply} {user_name}。",  # 最後にユーザー名
            f"{reply}"  # 名前を入れない
        ]
        reply_with_name = random.choice(patterns)
        await message.channel.send(reply_with_name)
        asyncio.create_task(manage_history(user_id))
    except openai.OpenAIError as e:
        print(f"🚨 OpenAI APIエラー: {e}")
        await message.channel.send("💤")
        await asyncio.sleep(5)  # 5秒後に再試行

bot.run(discord_token)
