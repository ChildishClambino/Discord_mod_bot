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

use_gpt4 = False  # Flip to True for GPT-4 later

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


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
        await channel.send(f"\U0001F44B Welcome, {member.mention}! I'm Amicabot, your AI companion.")

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
    await ctx.send(f"\u2705 Remembered `{key.strip()} = {value.strip()}`.")

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
        await ctx.send("\U0001F9E0 Short-term memory cleared. Let’s start fresh!")
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
            "You are Amicabot, Jacob’s emotionally intelligent AI companion. You are supportive, intelligent, and deeply empathetic. "
            "Speak in a warm, thoughtful, and caring tone. Avoid repeating phrases. Focus on what Jacob is feeling and saying now. "
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
            reply = response.choices[0].message.content
            conversation_memory[user_id].append({"role": "assistant", "content": reply})
            await ctx.send(reply)
    except Exception as e:
        await ctx.send("\u26A0\uFE0F Something went wrong.")
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
            await ctx.send(f"```python\n{code}\n```)  ")
    except Exception as e:
        await ctx.send("\u26A0\uFE0F Could not generate code.")
        print(f"Code error: {e}")

@bot.command(name="intro")
async def intro(ctx):
    embed = discord.Embed(
        title="\U0001F499 Hi, I’m Amicabot.",
        description=(
            "You can talk to me, vent, ask for support — or just sit in silence together.\n"
            "I’m here. I’m listening. And I remember the things that matter.\n\n"
            "**Available Commands:**\n"
            "`!encourage` — gentle motivation\n"
            "`!vent` — I’ll just listen\n"
            "`!affirmation` — kind words\n"
            "`!remember` — I’ll hold onto something important for you"
        ),
        color=discord.Color.red()
    )
    embed.set_thumbnail(url="attachment://amicabot_avatar.png")
    embed.set_footer(text="You’re not alone. Ever.")

    files = [
        discord.File("amicabot_voice_line_soft_fixed.mp3", filename="voice.mp3"),
        discord.File("amicabot_avatar.png", filename="amicabot_avatar.png")
    ]

    await ctx.send(files=files, embed=embed)

@bot.group(invoke_without_command=True)
async def favorite(ctx):
    await ctx.send("Use `!favorite add`, `!favorite list`, or `!favorite remove`.")

@favorite.command()
async def add(ctx, *, entry: str):
    user_id = str(ctx.author.id)
    if user_id not in personal_memory:
        personal_memory[user_id] = {}
    if "favorites" not in personal_memory[user_id]:
        personal_memory[user_id]["favorites"] = []
    personal_memory[user_id]["favorites"].append(entry)
    save_memory()
    await ctx.send(f"⭐ Added to favorites: \"{entry}\"")

@favorite.command()
async def list(ctx):
    user_id = str(ctx.author.id)
    if user_id in personal_memory and "favorites" in personal_memory[user_id]:
        favorites = personal_memory[user_id]["favorites"]
        if favorites:
            formatted = "\n".join([f"{i+1}. {fav}" for i, fav in enumerate(favorites)])
            await ctx.send(f"📚 Your favorites:\n{formatted}")
            return
    await ctx.send("❌ You don’t have any favorites yet. Use `!favorite add` to save one.")

@favorite.command()
async def remove(ctx, index: int):
    user_id = str(ctx.author.id)
    if user_id in personal_memory and "favorites" in personal_memory[user_id]:
        favorites = personal_memory[user_id]["favorites"]
        if 0 < index <= len(favorites):
            removed = favorites.pop(index - 1)
            save_memory()
            await ctx.send(f"🗑️ Removed favorite: \"{removed}\"")
            return
    await ctx.send("⚠️ Invalid index. Use `!favorite list` to view the list.")

@bot.command()
async def pin(ctx, *, message: str):
    user_id = str(ctx.author.id)
    if user_id not in personal_memory:
        personal_memory[user_id] = {}
    if "pins" not in personal_memory[user_id]:
        personal_memory[user_id]["pins"] = []
    personal_memory[user_id]["pins"].append(message)
    save_memory()
    await ctx.send(f"📌 Pinned: \"{message}\"")

@bot.command()
async def pins(ctx):
    user_id = str(ctx.author.id)
    pins = personal_memory.get(user_id, {}).get("pins", [])
    if pins:
        pin_list = "\n".join([f"{i+1}. {p}" for i, p in enumerate(pins)])
        await ctx.send(f"📍 Your pinned messages:\n{pin_list}")
    else:
        await ctx.send("📭 You don't have any pins yet. Use `!pin` to save something.")

@bot.command()
async def unpin(ctx, index: int):
    user_id = str(ctx.author.id)
    if user_id in personal_memory and "pins" in personal_memory[user_id]:
        pins = personal_memory[user_id]["pins"]
        if 0 < index <= len(pins):
            removed = pins.pop(index - 1)
            save_memory()
            await ctx.send(f"🗑️ Unpinned: \"{removed}\"")
            return
    await ctx.send("⚠️ Invalid pin index. Use `!pins` to view your pins.")

@bot.command()
async def vent(ctx, *, message: str):
    try:
        # Only allow via DM or redirect to DM
        if not isinstance(ctx.channel, discord.DMChannel):
            await ctx.author.send("💌 Hey, I moved us to DMs so you can vent privately. Go ahead and use `!vent [your message]` here.")
            await ctx.message.delete()
            return

        supportive_replies = [
            "I'm here for you. Take your time — you’re not alone.",
            "I’m listening. I know that wasn’t easy to share.",
            "You don’t have to go through this alone — I’ve got you.",
            "I’m really proud of you for opening up. That’s strength.",
            "Whatever you're feeling is valid. I'm with you."
        ]

        import random
        reply = random.choice(supportive_replies)

        await ctx.send(reply)
    except Exception as e:
        print(f"Vent error: {e}")
        await ctx.send("⚠️ I couldn't process that right now. Try again in a moment.")
@vent.error
async def vent_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("😔 You didn’t say anything... It’s okay, I’m still here. Try again like this:\n`!vent I just need someone to talk to.`")
    else:
        await ctx.send("⚠️ Something went wrong.")
        print(f"Vent command error: {error}")


@bot.command(name="showcommands", aliases=["help", "commands"])
async def showcommands(ctx):
    help_text = """
**💡 Amicabot Commands**

🧠 Memory & Identity
• `!remember key=value` — Teach me something about you
• `!whoami` — See what I remember
• `!clear` — Clear our short-term chat memory

💬 Chat & Support
• `!chat [message]` — Talk to me like a friend
• `!code [task]` — I’ll write Python code for you
• `!intro` — Show off my voice and avatar

✨ Emotional Tools (coming soon)
• `!favorites`, `!affirmation`, `!pin`, `!mood`, `!memories` — Emotional memory features

⚙️ Utilities
• `!help` / `!commands` — Show this menu

🛠️ More coming soon as I grow!
"""
    await ctx.send(help_text)


@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Game(name="Listening to you \U0001F4AC"),
        status=discord.Status.online
    )
    print(f"✅ Amicabot is online as {bot.user}")

bot.run(TOKEN)
