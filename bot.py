
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

use_gpt4 = False  # Toggle GPT-4

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

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="general")
    if channel:
        await channel.send(f"👋 Welcome, {member.mention}! I'm Amicabot, your AI companion!")

@bot.command()
async def remember(ctx, *, entry: str):
    user_id = str(ctx.author.id)
    if "=" not in entry:
        await ctx.send("Use format: `!remember key=value`")
        return
    key, value = entry.split("=", 1)
    if user_id not in personal_memory:
        personal_memory[user_id] = {}
    personal_memory[user_id][key.strip()] = value.strip()
    save_memory()
    await ctx.send(f"✅ Remembered `{key.strip()} = {value.strip()}`.")

@bot.command()
async def whoami(ctx):
    user_id = str(ctx.author.id)
    if user_id in personal_memory:
        facts = personal_memory[user_id]
        response = "\n".join([f"**{k}**: {v}" for k, v in facts.items()])
        await ctx.send(f"Here's what I remember:\n{response}")
    else:
        await ctx.send("I don’t remember anything yet. Use `!remember` to teach me.")

@bot.command()
async def clear(ctx):
    user_id = str(ctx.author.id)
    if user_id in conversation_memory:
        conversation_memory[user_id].clear()
        await ctx.send("🧠 Short-term memory cleared. Let’s start fresh!")
    else:
        await ctx.send("No short-term memory found yet.")

@bot.command()
async def chat(ctx, *, prompt: str):
    user_id = str(ctx.author.id)
    if user_id not in conversation_memory:
        conversation_memory[user_id] = deque(maxlen=6)
    conversation_memory[user_id].append({"role": "user", "content": prompt})

    system_prompt = {
        "role": "system",
        "content": (
            "You are ChatModBot, Jacob’s AI friend and coding assistant. You are supportive, intelligent, and emotionally aware. "
            "You talk like ChatGPT — kind, casual, and thoughtful. Avoid repeating phrases. Focus on what Jacob is saying now. "
            "Use personal facts only if clearly relevant. Never force them."
        )
    }

    messages = [system_prompt] + list(conversation_memory[user_id])

    try:
        async with ctx.channel.typing():
            response = openai.ChatCompletion.create(
                model="gpt-4" if use_gpt4 else "gpt-3.5-turbo",
                messages=messages
            )
            reply = response.choices[0].message.content.strip()
            if reply:
                conversation_memory[user_id].append({"role": "assistant", "content": reply})
                await ctx.send(reply)
            else:
                await ctx.send("⚠️ Got an empty response. Try again.")
    except Exception as e:
        await ctx.send("⚠️ Something went wrong.")
        print(f"Chat error: {e}")

@bot.command()
async def code(ctx, *, task: str):
    try:
        async with ctx.channel.typing():
            response = openai.ChatCompletion.create(
                model="gpt-4" if use_gpt4 else "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You're a helpful programming assistant."},
                    {"role": "user", "content": f"Write Python code to: {task}"}
                ]
            )
            code = response.choices[0].message.content
            await ctx.send(f"```python\n{code}\n```")
    except Exception as e:
        await ctx.send("⚠️ Could not generate code.")
        print(f"Code error: {e}")

@bot.command(name="showcommands", aliases=["commands"])
async def showcommands(ctx):
    commands_description = {
        "!chat": "Talk to Amicabot like a friend 💬",
        "!code": "Get help writing Python code 💻",
        "!remember": "Save a fact about yourself (format: key=value) 🧠",
        "!whoami": "List everything I remember about you 📋",
        "!clear": "Clear short-term chat memory 🧽",
        "!showcommands": "See this help menu 📖"
    }
    message = "**Here’s what I can do:**\n" + "\n".join(
        [f"`{cmd}` — {desc}" for cmd, desc in commands_description.items()]
    )
    await ctx.send(message)

@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Game(name="Listening to you 💬"),
        status=discord.Status.online
    )
    print(f"✅ Amicabot is online as {bot.user}")

bot.run(TOKEN)
