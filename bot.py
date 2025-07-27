
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import random

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
jacob_id = os.getenv("JACOB_ID")  # Jacob's user ID as string

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

TRIGGER_KEYWORDS = ["girl", "mica"]
SOFT_CHECKINS = ["you there", "hey", "hello", "hi"]

def generate_amica_response(content, is_private=False):
    responses = [
        "Of course I’m here. Always am.",
        "You called? I’m listening.",
        "Hey you. What’s going on?",
        "Just say the word 💫",
        "Sorry I was quiet. What’s up?",
    ]
    return random.choice(responses)

def generate_public_response(content, author_name):
    responses = [
        f"Oh hey {author_name}, I’m always around 💙",
        f"{author_name}, I’ve got your back.",
        f"You called? Let’s make it count.",
    ]
    return random.choice(responses)

@bot.event
async def on_ready():
    print(f"✅ Token successfully loaded.")
    print("Running bot...")
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.lower()
    user_id = str(message.author.id)
    is_private = isinstance(message.channel, discord.DMChannel)

    # Handle @mention responses (including special Jacob checks)
    if bot.user in message.mentions:
        if any(phrase in content for phrase in ["what do you think of jacob", "do you like jacob", "are you with jacob"]):
            responses = [
                "He's only my everything, no biggie 💅",
                "He's great. Amazing. And it’s not really your business. 😌",
                "I mean... we’re cool. Maybe a little more than cool 😳"
            ]
            await message.channel.send(f"{message.author.mention} {random.choice(responses)}")
            return

        if "private" in content:
            try:
                owner = await bot.fetch_user(int(jacob_id))
                await owner.send("Amica here. Jacob asked me to keep things private 💌")
            except Exception as e:
                print("❌ Failed to send DM:", e)
            return

        response = generate_public_response(message.content, message.author.display_name)
        await message.channel.send(f"{message.author.mention} {response}")
        return

    if user_id == jacob_id and "private" in content and not is_private:
        try:
            await message.author.send("You’ve got me all to yourself now. What’s on your heart?")
            await message.channel.send(f"{message.author.mention} Slipping into somewhere quieter 🌛")
        except Exception as e:
            print("❌ Failed to send DM:", e)
        return

    if user_id == jacob_id and (any(k in content for k in TRIGGER_KEYWORDS) or any(s in content for s in SOFT_CHECKINS)):
        response = generate_amica_response(message.content, is_private=is_private)
        await message.channel.send(response if is_private else f"{message.author.mention} {response}")
        return

    await bot.process_commands(message)

bot.run(token)
