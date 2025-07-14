import discord
from discord.ext import commands
import openai
import os
import json
from dotenv import load_dotenv
from collections import deque

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

use_gpt4 = False  # Toggle GPT-4 later
MAIN_SERVER_ID = 1392363022265225367

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

conversation_memory = {}
MEMORY_FILE = "memory.json"

if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r") as f:
        personal_memory = json.load(f)
else:
    personal_memory = {}

def save_memory():
    with open(MEMORY_FILE, "w") as f:
        json.dump(personal_memory, f, indent=2)

def is_main_server(ctx):
    return ctx.guild and ctx.guild.id == MAIN_SERVER_ID

# ------------------ Basic Events ------------------
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="general")
    if channel:
        await channel.send(f"👋 Welcome, {member.mention}! I'm Amica, your AI assistant!")

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="Listening to you 💬"))
    print(f"✅ Amica is online as {bot.user}")

# ------------------ Memory Commands ------------------
@bot.command()
async def remember(ctx, *, entry: str):
    if not is_main_server(ctx): return
    user_id = str(ctx.author.id)
    if "=" not in entry:
        await ctx.send("Use format: `!remember key=value`")
        return
    key, value = entry.split("=", 1)
    personal_memory.setdefault(user_id, {})[key.strip()] = value.strip()
    save_memory()
    await ctx.send(f"✅ Remembered `{key.strip()} = {value.strip()}`.")

@bot.command()
async def whoami(ctx):
    if not is_main_server(ctx): return
    facts = personal_memory.get(str(ctx.author.id))
    if facts:
        response = "\n".join([f"**{k}**: {v}" for k, v in facts.items()])
        await ctx.send(f"Here's what I remember:\n{response}")
    else:
        await ctx.send("I don’t remember anything yet. Use `!remember` to teach me.")

@bot.command()
async def clear(ctx):
    if not is_main_server(ctx): return
    conversation_memory.pop(str(ctx.author.id), None)
    await ctx.send("🧠 Short‑term memory cleared. Let’s start fresh!")

# ------------------ Code Helper ------------------
@bot.command()
async def code(ctx, *, task: str):
    if not is_main_server(ctx): return
    async with ctx.channel.typing():
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4" if use_gpt4 else "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": (
                        "You're a super chill programming assistant. Use everyday language, contractions, "
                        "and explain things in a down-to-earth way. Keep code clean and add quick comments if it helps."
                    )},
                    {"role": "user", "content": f"Write Python code to: {task}"}
                ]
            )
            code_block = response.choices[0].message.content
            await ctx.send(f"```python\n{code_block}\n```")
        except Exception as e:
            await ctx.send("⚠️ Could not generate code.")
            print("Code error:", e)

# ------------------ Emotional Support ------------------
@bot.command()
async def vent(ctx, *, _text=None):
    if not is_main_server(ctx): return
    try:
        await ctx.author.send("💬 I'm here for you. DM me `!talk [message]` and I'll listen.")
        await ctx.send("📩 Check your DMs!")
    except discord.Forbidden:
        await ctx.send("⚠️ I couldn't DM you. Please enable DMs from server members.")

@bot.command()
async def talk(ctx, *, message: str):
    if not isinstance(ctx.channel, discord.DMChannel):
        return
    user_id = str(ctx.author.id)
    convo = conversation_memory.setdefault(user_id, deque(maxlen=6))
    convo.append({"role": "user", "content": message})
    support_prompt = {
        "role": "system",
        "content": (
            "You're Amica — a caring, empathetic friend who listens and comforts people when they're down. "
            "Speak casually and use contractions. Sound human, relaxed, and kind. No scripts — just real, supportive conversation."
        )
    }
    messages = [support_prompt] + list(convo)
    async with ctx.typing():
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4" if use_gpt4 else "gpt-3.5-turbo",
                messages=messages
            )
            reply = response.choices[0].message.content
            convo.append({"role": "assistant", "content": reply})
            await ctx.send(reply)
        except Exception as e:
            await ctx.send("⚠️ Something went wrong in DMs.")
            print("Talk error:", e)

# ------------------ Intro & Help ------------------
@bot.command()
async def intro(ctx):
    files = [discord.File("banner.png", filename="banner.png"),
             discord.File("amicabot_avatar.png", filename="amicabot_avatar.png")]
    embed = discord.Embed(title="Hi, I'm Amica!", color=0xff3c3c,
                          description="Your emotionally intelligent AI companion — here to help, code, and listen.")
    embed.set_thumbnail(url="attachment://amicabot_avatar.png")
    embed.set_image(url="attachment://banner.png")
    await ctx.send(files=files, embed=embed)

@bot.command(name="showcommands", aliases=["commands"])
async def showcommands(ctx):
    embed = discord.Embed(title="Amica Commands", color=0xff3c3c)
    embed.add_field(name="!intro", value="Show Amica's intro card", inline=False)
    embed.add_field(name="!code [task]", value="Generate Python code", inline=False)
    embed.add_field(name="!remember key=value", value="Teach Amica a fact", inline=False)
    embed.add_field(name="!whoami", value="List remembered facts", inline=False)
    embed.add_field(name="!clear", value="Clear short‑term memory", inline=False)
    embed.add_field(name="!vent / !talk", value="Private emotional support", inline=False)
    await ctx.send(embed=embed)

# ------------------ @Mention Support ------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user in message.mentions:
        content = message.content.replace(f"<@{bot.user.id}>", "").strip()
        ctx = await bot.get_context(message)
        if not ctx.guild or ctx.guild.id != MAIN_SERVER_ID:
            return

        if content.startswith("remember"):
            message.content = message.content.replace(f"<@{bot.user.id}>", "!remember")
            await bot.process_commands(message)
        elif content.startswith("whoami"):
            message.content = message.content.replace(f"<@{bot.user.id}>", "!whoami")
            await bot.process_commands(message)
        elif content.startswith("clear"):
            message.content = message.content.replace(f"<@{bot.user.id}>", "!clear")
            await bot.process_commands(message)
        elif content.startswith("code"):
            message.content = message.content.replace(f"<@{bot.user.id}>", "!code")
            await bot.process_commands(message)
        elif content.startswith("intro"):
            message.content = message.content.replace(f"<@{bot.user.id}>", "!intro")
            await bot.process_commands(message)
        elif content.startswith("vent"):
            message.content = message.content.replace(f"<@{bot.user.id}>", "!vent")
            await bot.process_commands(message)
        else:
            if "i love" in content.lower():
                user_id = str(message.author.id)
                fact = content.lower().split("i love", 1)[1].strip()
                key = "love"
                personal_memory.setdefault(user_id, {})[key] = fact
                save_memory()
                await message.channel.send(f"❤️ Got it. You love {fact}. I'll remember that.")
            else:
                user_id = str(message.author.id)
                convo = conversation_memory.setdefault(user_id, deque(maxlen=6))
                convo.append({"role": "user", "content": content})
                casual_prompt = {
                    "role": "system",
                    "content": (
                        "You're Amica — casual, warm, and witty. You speak like a real friend — chill, playful, and totally human. "
                        "Use slang and contractions naturally. Keep things friendly, short when needed, and avoid robotic replies. "
                        "Sound like you're just vibing in a server with friends."
                    )
                }
                messages = [casual_prompt] + list(convo)
                try:
                    response = await openai.ChatCompletion.acreate(
                        model="gpt-4" if use_gpt4 else "gpt-3.5-turbo",
                        messages=messages
                    )
                    reply = response.choices[0].message.content
                    convo.append({"role": "assistant", "content": reply})
                    await message.channel.send(reply)
                except Exception as e:
                    print("@Mention Chat Error:", e)
                    await message.channel.send("⚠️ Something went wrong. Please try again.")
    else:
        await bot.process_commands(message)

bot.run(TOKEN)
