import discord
import openai
import asyncio
import os
from discord.ext import commands
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
intents.message_content = True  # メッセージの内容を取得できるようにする

bot = commands.Bot(command_prefix="!", intents=intents)

# 会話履歴の保存用（ユーザーごとに管理）
conversation_history = {}

# ギルドごとのキャラクター設定（リスト形式で複数の設定を保持）
character_settings = {}

# 会話履歴の保持時間（秒）
HISTORY_EXPIRATION = 300  # 5分間

async def manage_history(user_id):
    """一定時間後に会話履歴を削除"""
    await asyncio.sleep(HISTORY_EXPIRATION)
    if user_id in conversation_history:
        del conversation_history[user_id]

@bot.event
async def on_ready():
    print(f"✅ ログインしました: {bot.user}")

@bot.command()
async def set_character(ctx, *, setting: str):
    """ギルド全体のキャラクター設定を追記するコマンド"""
    guild_id = ctx.guild.id
    if guild_id not in character_settings:
        character_settings[guild_id] = []
    character_settings[guild_id].append(setting)
    await ctx.send(f"キャラクター設定を追加しました: {setting}")

@bot.command()
async def list_character(ctx):
    """現在のギルドのキャラクター設定を一覧表示するコマンド"""
    guild_id = ctx.guild.id
    settings = character_settings.get(guild_id, ["デフォルト設定: 『サイカワ』です。『桝見荘』の管理人代行をしています。"])
    await ctx.send("現在のキャラクター設定:\n" + "\n".join(settings))

@bot.command()
async def save_character(ctx):
    """現在のギルドのキャラクター設定を .txt ファイルに保存するコマンド"""
    guild_id = ctx.guild.id
    settings = character_settings.get(guild_id, ["デフォルト設定: 『サイカワ』です。『桝見荘』の管理人代行をしています。"])
    filename = f"character_settings_{guild_id}.txt"
    with open(filename, "w", encoding="utf-8") as file:
        file.write("\n".join(settings))
    await ctx.send(f"キャラクター設定を `{filename}` に保存しました。")

@bot.command()
async def upload_character(ctx):
    """ユーザーがアップロードした .txt ファイルをキャラクター設定として上書きするコマンド"""
    if not ctx.message.attachments:
        await ctx.send("ファイルが添付されていません。")
        return
    
    attachment = ctx.message.attachments[0]
    if not attachment.filename.endswith(".txt"):
        await ctx.send(".txt ファイルをアップロードしてください。")
        return
    
    guild_id = ctx.guild.id
    content = await attachment.read()
    settings = content.decode("utf-8").split("\n")
    character_settings[guild_id] = [setting.strip() for setting in settings if setting.strip()]
    
    await ctx.send("キャラクター設定をアップロードしたファイルの内容に更新しました。")

@bot.command()
async def reset_character(ctx):
    """キャラクター設定をリセットするコマンド"""
    guild_id = ctx.guild.id
    character_settings[guild_id] = []
    await ctx.send("キャラクター設定をリセットしました。")

@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Bot自身のメッセージは無視
    
    # コマンド処理を優先
    if await bot.process_commands(message):
        return  # コマンドが処理された場合は、通常のメッセージ処理をスキップ
    
    if bot.user not in message.mentions:
        return  # メンションされていない場合は無視
    
    user_id = message.author.id
    user_name = message.author.display_name  # サーバー内の表示名を取得
    guild_id = message.guild.id if message.guild else None

    # 履歴がなければ初期化
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    # ユーザーの過去の発言を保存
    conversation_history[user_id].append({"role": "user", "content": message.content})

    # OpenAI API に送るメッセージリストを作成
    system_messages = character_settings.get(guild_id, ["あなたは『サイカワ』です。『桝見荘』の管理人代行をしています。"])
    messages = [{"role": "system", "content": setting} for setting in system_messages]
    messages.extend(conversation_history[user_id])

    # OpenAI API を使用して返答を生成
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )

        reply = response.choices[0].message.content

        # 返答を履歴に保存
        conversation_history[user_id].append({"role": "assistant", "content": reply})

        # ユーザー名を呼びながら返信
        reply_with_name = f"{user_name}様、{reply}"
        await message.channel.send(reply_with_name)

        # 履歴管理タスクをスケジュール
        asyncio.create_task(manage_history(user_id))

    except Exception as e:
        print(f"🚨 OpenAI APIエラー: {e}")
        await message.channel.send("申し訳ありませんが、現在応答できません。")

# Botの実行
bot.run(discord_token)
