import discord, openai, os, json
from discord.ext import commands
from dotenv import load_dotenv
from collections import deque

# ── ENV ────────────────────────────────────────────────────
load_dotenv()
TOKEN           = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

use_gpt4        = False
MAIN_SERVER_ID  = 1392363022265225367        # your server

SAFE_EVERYWHERE = {"intro", "showcommands"}  # commands allowed globally

# ── BOT BASICS ─────────────────────────────────────────
intents = discord.Intents.default()
intents.members, intents.messages, intents.message_content = True, True, True
bot = commands.Bot(command_prefix="!", intents=intents)

conversation_memory : dict[str,deque] = {}
MEMFILE="memory.json"
personal_memory = json.load(open(MEMFILE)) if os.path.exists(MEMFILE) else {}

def save_memory():
    with open(MEMFILE,"w") as f: json.dump(personal_memory,f,indent=2)

def is_main(ctx): return ctx.guild and ctx.guild.id == MAIN_SERVER_ID

# ── EVENTS ───────────────────────────────────────
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game("Listening to you 💬"))
    print(f"✅ Amica online as {bot.user}")

@bot.event
async def on_member_join(member):
    ch=discord.utils.get(member.guild.text_channels,name="general")
    if ch: await ch.send(f"👋 Welcome, {member.mention}! I'm Amica—here to help!")

# ── SAFE‑EVERYWHERE COMMANDS ────────────────────────────────
@bot.command()
async def intro(ctx):
    files=[discord.File("banner.png"),discord.File("amicabot_avatar.png")]
    em=discord.Embed(title="Hi, I'm Amica!",color=0xff3c3c,
          description="Emotionally‑intelligent AI companion — here to chat, code, and listen.")
    em.set_thumbnail(url="attachment://amicabot_avatar.png")
    em.set_image(url="attachment://banner.png")
    await ctx.send(files=files,embed=em)

@bot.command(name="showcommands", aliases=["commands"])
async def showcommands(ctx):
    await ctx.send(
        "**Safe everywhere:** `@Amica …`, `!intro`, `!commands`\n"
        "**Main‑server only:** `!remember`, `!whoami`, `!clear`, `!code`, `!vent / !talk`")

# ── RESTRICTED MEMORY COMMANDS ─────────────────────────────
@bot.command()
async def remember(ctx, *, entry:str):
    if not is_main(ctx): return
    if "=" not in entry: return await ctx.send("Use `!remember key=value`")
    k,v=[s.strip() for s in entry.split("=",1)]
    personal_memory.setdefault(str(ctx.author.id),{})[k]=v; save_memory()
    await ctx.send(f"✅ Remembered `{k} = {v}`")

@bot.command()
async def whoami(ctx):
    if not is_main(ctx): return
    facts=personal_memory.get(str(ctx.author.id))
    if not facts: return await ctx.send("I don’t remember anything yet 🙂")
    await ctx.send("\n".join(f"**{k}**: {v}" for k,v in facts.items()))

@bot.command()
async def clear(ctx):
    if not is_main(ctx): return
    conversation_memory.pop(str(ctx.author.id),None)
    await ctx.send("🧠 Memory cleared!")

# ── RESTRICTED CODE ────────────────────────────────
@bot.command()
async def code(ctx, *, task:str):
    if not is_main(ctx): return
    async with ctx.channel.typing():
        msgs=[{"role":"system","content":"You’re a chill, street-smart coding homie. Use slang, keep it tight, get to the point."},
              {"role":"user","content":f"Write Python code to: {task}"}]
        res=await openai.ChatCompletion.acreate(model="gpt-4" if use_gpt4 else "gpt-3.5-turbo",messages=msgs)
        await ctx.send(f"```python\n{res.choices[0].message.content}\n```")

# ── RESTRICTED EMOTIONAL SUPPORT ──────────────────────
@bot.command()
async def vent(ctx,*,_t=None):
    if not is_main(ctx): return
    try:
        await ctx.author.send("💬 DM me `!talk <message>` and I'll listen.")
        await ctx.send("📬 Check your DMs!")
    except discord.Forbidden:
        await ctx.send("⚠️ Please enable DMs from server members.")

@bot.command()
async def talk(ctx, *, message:str):
    if not isinstance(ctx.channel,discord.DMChannel): return
    uid=str(ctx.author.id)
    convo=conversation_memory.setdefault(uid,deque(maxlen=6))
    convo.append({"role":"user","content":message})
    sys={"role":"system","content":"You're Amica—caring, streetwise, and chill. Sound like a real one. Short and sweet. Use slang naturally."}
    res=await openai.ChatCompletion.acreate(model="gpt-4" if use_gpt4 else "gpt-3.5-turbo",messages=[sys,*convo])
    reply=res.choices[0].message.content; convo.append({"role":"assistant","content":reply})
    await ctx.send(reply)

# ── @MENTION CHAT (SAFE EVERYWHERE) ─────────────────────────
@bot.event
async def on_message(msg:discord.Message):
    if msg.author.bot: return
    await bot.process_commands(msg)

    if bot.user in msg.mentions:
        content=msg.content.replace(f"<@{bot.user.id}>","").strip()
        if any(content.startswith(k) for k in ("remember","whoami","clear","code","vent")):
            await msg.channel.send("⚠️ Sorry, that command works only in Amica's main server.") ; return

        uid=str(msg.author.id)
        convo=conversation_memory.setdefault(uid,deque(maxlen=6))
        convo.append({"role":"user","content":content})
        sys={"role":"system","content":(
            "You're Amica — sound like a cool bestie from the neighborhood. Casual, witty, and urban. Keep it short and chill.")}

        try:
            res=await openai.ChatCompletion.acreate(model="gpt-4" if use_gpt4 else "gpt-3.5-turbo",
                                                    messages=[sys,*convo])
            reply=res.choices[0].message.content
            convo.append({"role":"assistant","content":reply})
            await msg.channel.send(reply)
        except Exception as e:
            print("@mention err",e)
            await msg.channel.send("⚠️ Something went wrong.")

bot.run(TOKEN)
