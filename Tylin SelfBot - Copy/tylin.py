import discord
from discord.ext import commands, tasks
import asyncio
import random
import requests
import shlex
import aiohttp
import threading
from collections import deque
import websockets
import time
import json
import os
from datetime import datetime, timezone, timedelta
from tls_client import Session
import tls_client
import base64
import hashlib
import math
from urllib.parse import urlencode
from urllib.request import urlretrieve
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap
import io
from pystyle import Center, Colors, Colorate
import itertools


token= 'ADD TOKEN HERE'

YLIN = commands.Bot(command_prefix=".", intents=discord.Intents.all(), self_bot=True, help_command=None)


ar2file = 'ar2.txt'
if not os.path.exists(ar2file):
    with open(ar2file, 'w') as f:
        pass
              
def newlines(text):
    return text.replace('\n', '\\n')

def newline(text):
    return text.replace('\\n', '\n')

def loadar2():
    ar2users = {}
    with open(ar2file, 'r') as f:
        for line in f:
            if line.strip():
                user_id, username, message = line.strip().split(" | ", 2)
                ar2users[int(user_id)] = (username, newline(message))
    return ar2users

def savear2(ar2users):
    with open(ar2file, 'w') as f:
        for user_id, (username, message) in ar2users.items():
            f.write(f"{user_id} | {username} | {newlines(message)}\n")           

arfile = 'ar.txt'
if not os.path.exists(arfile):
    with open(arfile, 'w') as f:
        pass

def loadar():
    global ar_users, ar_active
    ar_users.clear()
    
    with open(arfile, 'r') as f:
        for line in f:
            if line.strip():
                user_id = int(line.strip())
                ar_users.add(user_id)

    ar_active = bool(ar_users)

def savear():
    with open(arfile, 'w') as f:
        for user_id in ar_users:
            f.write(f"{user_id}\n")
            
with open('send.txt', 'r') as file:
    send = [line.strip() for line in file]    

with open('press.txt', 'r') as file:
    press = [line.strip() for line in file]
 
with open('press.txt', 'r') as file:
    press2 = [line.strip() for line in file]

  
emojisreact = []
reaction_active = False
react_queue = deque()
emojip = None
rate_limit_lock = asyncio.Lock()
autoreply_enabled = False
tasks = {}
reply_queue = deque()
reply_active = True
ar_active = False
ar_users = set()
gcstatus = {}
ap = False
auto_replies = {}
ar2users = loadar2()
auto_reply_enabled = {user_id: True for user_id in ar2users}
auto_replies.update({user_id: message for user_id, (_, message) in ar2users.items()})
ap2 = False
stfu_users = {}
spamregion_task = None
start_time = datetime.now(timezone.utc)
statusr = False
statuses = []
statusi = 0
ab = False
rgid = []
rga = False
rspam = False
auto_adder_enabled = False
gc_id = None
user_ids = []

# ── ar1: fixed autoreply to specific users ──
ar1_active = False
ar1_targets = {}  # user_id → fixed reply message (str)


async def react_task(message, emoji):
    react_queue.append((message, emoji))

async def replytask(message, reply):
    reply_queue.append((message, reply))


@YLIN.event
async def on_ready():
    global session
    os.system('cls' if os.name == 'nt' else 'clear')

    user = f"Welcome : {str(YLIN.user.name)[:25]:<25}"
    prefix = f"Prefix  : {str(YLIN.command_prefix):<25}"
    ver = f"Version : Dev"
    server = f"Servers : {len(YLIN.guilds):<25}"
    friend = f"Friends : {len(YLIN.user.friends):<25}"

    box_width = 35
    border_line = "═" * (box_width + 2)

    info_box = f"""                                                                             
╔═════════════════════════════════════╗
║             TYLIN                   ║
║          By TYLIN/TYE               ║ 
╚═════════════════════════════════════╝
╔{border_line}╗
║ {user} ║
║ {prefix} ║
║ {ver}                       ║
║ {server} ║
║ {friend} ║ 
╚{border_line}╝
    """

    chosen_color = random.choice([Colors.red_to_yellow, Colors.blue_to_cyan, Colors.green_to_blue])
    colored_info_box = Colorate.Horizontal(chosen_color, info_box, 1)

    os.system('cls' if os.name == 'nt' else 'clear')
    print(colored_info_box)

    loadar()


@YLIN.event
async def on_message(message):
    global auto_reply_enabled, reaction_active, ar_users

    if reaction_active and message.author.id == YLIN.user.id:
        chosen_emoji = emojir()
        if chosen_emoji:
            await react_task(message, chosen_emoji)

    if message.author == YLIN.user:
        await YLIN.process_commands(message)
        
    if message.author == YLIN.user:
        return

    if ar_active and message.author.id in ar_users:
        reply = random.choice(send)
        await replytask(message, reply)      

    if message.author == YLIN.user:
        return
        
    if message.author.id in stfu_users:
        await message.delete()        
        
    if message.author == YLIN.user:
        return

    if message.author.id in auto_replies and auto_reply_enabled.get(message.author.id, False):
        fr = auto_replies[message.author.id]
        try:
            await message.reply(f"{fr}")
            await asyncio.sleep(1.3)
        except discord.HTTPException as e:
        	pass

    # ── ar1: fixed autoreply to specific users ──
    if ar1_active and message.author.id in ar1_targets:
        reply_text = ar1_targets[message.author.id]
        try:
            await message.reply(reply_text)
            await asyncio.sleep(1.2)  # small delay to reduce rate-limit risk
        except discord.HTTPException:
            pass  # silent fail

    # ────────────────────────────────────────────────
    #             CHATPACK REPLY MODE LOGIC
    # ────────────────────────────────────────────────
    global chatpack_task, chatpack_channel, chatpack_target_user, chatpack_base_delay

    if chatpack_task and not chatpack_task.done():
        if chatpack_target_user is not None:
            if message.author.id == chatpack_target_user and message.channel.id == chatpack_channel.id:
                try:
                    with open("chatpack.txt", "r", encoding="utf-8") as f:
                        lines = [line.strip() for line in f if line.strip()]
                    if lines:
                        spam_line = random.choice(lines)
                        await message.reply(f"<@{chatpack_target_user}> {spam_line}", mention_author=True)

                        variation = max(0.6, chatpack_base_delay * 0.4)
                        min_d = max(0.7, chatpack_base_delay - variation)
                        max_d = chatpack_base_delay + variation
                        await asyncio.sleep(random.uniform(min_d, max_d))
                except Exception:
                    pass

    await YLIN.process_commands(message)


async def sendmsg(channel_id, message):
    channel = YLIN.get_channel(channel_id)
    await channel.send(message)
       

async def ladder_send(channel_id, message):
    parts = shlex.split(message)
    for part in parts:
        await sendmsg(channel_id, part)


async def aptask(channel, apuser, press, delay):
    while ap:
        reply = random.choice(press)
        mentions = " ".join(f"<@{user.id}>" for user in apuser)
        message = f'{reply} {mentions}'
        
        try:
            await channel.send(message)
        except discord.Forbidden:
            continue
        except Exception as e:
            print(f"An error occurred: {e}")
        
        await asyncio.sleep(delay)


async def ap2task(ctx, message):
    global ap2
    counter = 1
    channel = ctx.channel

    while ap2:
        try:
            await channel.send(f"{message} {counter}")
        except discord.Forbidden:
            continue
        except Exception as e:
            print(f"An error occurred: {e}")

        counter += 1
        await asyncio.sleep(3)


async def reacttask():
    while True:
        if react_queue and reaction_active:
            message, emoji = react_queue.popleft()
            try:
                if message.type == discord.MessageType.default:
                    async with rate_limit_lock:
                        await message.add_reaction(emoji)
            except discord.HTTPException as e:
                print(f"Error reacting to message: {e}")
        await asyncio.sleep(0.4)
        
        
def emojir():
    global emojip
    if not emojisreact:
        return None

    random.shuffle(emojisreact)

    for emoji in emojisreact:
        if emoji != emojip:
            emojip = emoji
            return emoji

    return random.choice(emojisreact)
        
        
async def artask():
    while True:
        if reply_queue and reply_active:
            message, reply = reply_queue.popleft()
            if message.type == discord.MessageType.default:
                channel = message.channel
                try:
                    async with rate_limit_lock:
                        await message.reply(reply)
                except discord.errors.HTTPException as e:
                    print(f'Failed to reply: {e}')
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f'Failed to reply: {e}')
                    await asyncio.sleep(2)
        await asyncio.sleep(1.3)
 

async def ustream():
    global statusi, statusc, statuses
    
    if statuses:
        await YLIN.change_presence(
            activity=discord.Streaming(name=statuses[statusi], url="https://www.twitch.tv/interlude"),
            status=discord.Status.dnd
        )
        statusi = (statusi + 1) % len(statuses)
    
    await asyncio.sleep(9)


@YLIN.command()
async def help(ctx, cmd_name: str = None):
    await ctx.message.delete()

    if not cmd_name:
        await ctx.send("Please provide a command name. Usage: `ask tylin for help`", delete_after=10)
        return

    cmd = YLIN.get_command(cmd_name)
    if not cmd:
        await ctx.send(f"No command named '{cmd_name}' found.", delete_after=10)
        return

    msg = f"```js\nCommand Help: {cmd.qualified_name}\n\n"
    msg += f"Usage: {cmd.qualified_name} {cmd.signature}\n"
    if cmd.aliases:
        msg += f"Aliases: {', '.join(cmd.aliases)}\n"
    msg += "```"

    await ctx.send(msg, delete_after=60)
    
        
@YLIN.command(aliases=['react'])
async def r(ctx, *emojis):
    await ctx.message.delete()
    global emojisreact, reaction_active

    if not emojis:
        await ctx.send("Please specify at least one emoji.", delete_after=5)
        return

    emojisreact = list(emojis)

    if reaction_active:
        # Optional: keep a short ephemeral-style feedback
        await ctx.send(f"Updated reaction emojis to: {', '.join(emojis)}", delete_after=4)
        print(f"Updated → {', '.join(emojis)}")
    else:
        reaction_active = True
        print(f"Started reacting with: {', '.join(emojis)}")
        # ← no ctx.send() here = no popup message at all
        

@YLIN.command(aliases=['re', 'endr', 'stopr', 'stopreact'])
async def sr(ctx):
    global emojisreact, reaction_active
    if not reaction_active:
        await ctx.send("Not currently reacting.")
        print("Not currently reacting.")
        return
    emojisreact = []
    reaction_active = False
    confirmation_message = await ctx.send("Stopped reacting.")
    await asyncio.sleep(1)
    await confirmation_message.delete()
    print("Stopped reacting.")


@YLIN.command()
async def ss(ctx, url: str):
    await ctx.message.delete()

    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    params = urlencode({
        "access_key": "find it by yourself",
        "url": url,
        "wait_until": "page_loaded"
    })
    image_path = "YLIN.png"

    try:
        urlretrieve(f"https://api.apiflash.com/v1/urltoimage?{params}", image_path)
        await ctx.send(file=discord.File(image_path))
        os.remove(image_path)
    except Exception as e:
        await ctx.send(f"Error generating screenshot: {e}")
        

@YLIN.command()
async def menu(ctx, page: int = 1):
    await ctx.message.delete()

    cmds = sorted([c for c in YLIN.commands if not c.hidden], key=lambda c: c.qualified_name.lower())
    per_page = 40
    total = len(cmds)
    pages = math.ceil(total / per_page)

    if page < 1 or page > pages:
        await ctx.send(f"Page {page} doesn't exist. Total pages: {pages}.", delete_after=10)
        return

    start = (page - 1) * per_page
    end = start + per_page
    page_cmds = cmds[start:end]

    left = page_cmds[:20]
    right = page_cmds[20:]

    header = f"```js\n[YLIN Sb]\n``````js"
    cmd_section = "\n"

    for i in range(20):
        l = f"[{str(start + i + 1).zfill(2)}] {left[i].qualified_name}" if i < len(left) else ""
        r = f"[{str(start + i + 21).zfill(2)}] {right[i].qualified_name}" if i < len(right) else ""
        cmd_section += f"{l.ljust(24)}│ {r}\n"

    cmd_section += "``````js"

    footer_text = "Creator - TYLIN/YLIN"
    footer = f"\n{footer_text.center(40)}\n```"

    await ctx.send(f"{header}\n{cmd_section}\n{footer}", delete_after=60)
    

@YLIN.command()
async def stream(ctx, *, statuses_list: str):
    global statuses, statusr, statusi

    await ctx.message.delete()

    statuses = [status.strip() for status in statuses_list.split(',')]
    statusi = 0

    if not statusr:
        statusr = True
        await ctx.send(f"Set Status to {statuses_list}", delete_after=3)

        while statusr:
            await ustream()
    else:
        await ctx.send(f"Status rotation is already running!", delete_after=3)

@YLIN.command()
async def streamoff(ctx):
    global statusr

    await ctx.message.delete()

    if statusr:
        statusr = False
        await YLIN.change_presence(activity=None, status=discord.Status.invisible)
        await ctx.send(f"```Status rotation stopped```", delete_after=3)
    else:
        await ctx.send(f"```Status rotation is not running```", delete_after=3)


@YLIN.command()
async def tti(ctx, *, txt: str):
    await ctx.message.delete()

    w, h = 3698, 2080
    fpath = "YLIN.ttf"

    try:
        words = txt.split()
        long = len(words) > 5
        size, min_size = 300 if not long else 200, 150

        while size > min_size:
            font = ImageFont.truetype(fpath, size)
            lines = textwrap.wrap(txt, width=50 if long else 20)
            total_h = sum(font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines) + (len(lines) - 1) * 10
            if total_h < h - 40:
                break
            size -= 5

        img = Image.new("RGB", (w, h), "black")
        d = ImageDraw.Draw(img)
        g = Image.new("RGB", (w, h), "black")
        gd = ImageDraw.Draw(g)
        font = ImageFont.truetype(fpath, size)
        lines = textwrap.wrap(txt, width=50 if long else 20)
        total_h = sum(font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines) + (len(lines) - 1) * 10
        x, y = (80, (h - total_h) // 2) if not long else (40, 40)

        glow = (255, 255, 255)
        for line in lines:
            tw = font.getbbox(line)[2] - font.getbbox(line)[0]
            if not long:
                tx = (w - tw) // 2
                gd.text((tx, y), line, font=font, fill=glow)
                d.text((tx, y), line, font=font, fill="white")
                y += font.getbbox(line)[3] - font.getbbox(line)[1] + 10
            else:
                if x + tw > w - 40:
                    x, y = 40, y + font.getbbox(line)[3] - font.getbbox(line)[1] + 10
                gd.text((x, y), line, font=font, fill=glow)
                d.text((x, y), line, font=font, fill="white")
                x += tw + 10

        g = g.filter(ImageFilter.GaussianBlur(10))
        final = Image.blend(img, g, 0.6)

        path = "YLIN.png"
        final.save(path)
        await ctx.send(file=discord.File(path))
        os.remove(path)

    except IOError:
        await ctx.send("Font file YLIN.ttf not found.", delete_after=5)
        
        
@YLIN.command()
async def stfu(ctx, member: discord.Member):
    if member.id not in stfu_users:
        stfu_users[member.id] = True
        await ctx.send(f"{member.mention} has auto delete on them ")
    else:
        await ctx.send(f"{member.mention} has auto delete on them already")

@YLIN.command()
async def stfuoff(ctx, member: discord.Member):
    if member.id in stfu_users:
        del stfu_users[member.id]
        await ctx.send(f"{member.mention} auto delete has been turned off")
    else:
        await ctx.send(f"{member.mention} doesn't have auto delete on them ")


@YLIN.command()
async def setname(ctx, *, name: str = None):
    if not name:
        await ctx.send("```Please provide a name to set```", delete_after=5)
        return

    await ctx.message.delete()    
    
    headers = {
            "authority": "discord.com",
            "method": "PATCH",
            "scheme": "https",
            "accept": "/",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US",
            "authorization": token,
            "origin": "https://discord.com/",
            "sec-ch-ua": '"Not/A)Brand";v="99", "Brave";v="115", "Chromium";v="115"',
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9020 Chrome/108.0.5359.215 Electron/22.3.26 Safari/537.36",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "X-Debug-Options": "bugReporterEnabled",
            "X-Discord-Locale": "en-US",
            "X-Discord-Timezone": "Asia/Calcutta",
            "X-Super-Properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiRGlzY29yZCBDbGllbnQiLCJyZWxlYXNlX2NoYW5uZWwiOiJzdGFibGUiLCJjbGllbnRfdmVyc2lvbiI6IjEuMC45MDIwIiwib3NfdmVyc2lvbiI6IjEwLjAuMTkwNDUiLCJvc19hcmNoIjoieDY0IiwiYXBwX2FyY2giOiJpYTMyIiwic3lzdGVtX2xvY2FsZSI6ImVuLVVTIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV09XNjQpIEFwcGxlV2ViS2l0LzUzNy4zNiAoS0hUTUwsIGxpa2UgR2Vja28pIGRpc2NvcmQvMS4wLjkwMjAgQ2hyb21lLzEwOC4wLjUzNTkuMjE1IEVsZWN0cm9uLzIyLjMuMjYgU2FmYXJpLzUzNy4zNiIsImJyb3dzZXJfdmVyc2lvbiI6IjIyLjMuMjYiLCJjbGllbnRfYnVpbGRfbnVtYmVyIjoyNDAyMzcsIm5hdGl2ZV9idWlsZF9udW1iZXIiOjM4NTE3LCJjbGllbnRfZXZlbnRfc291cmNlIjpudWxsLCJkZXNpZ25faWQiOjB9"
        }

    payload = {
        "global_name": name
    }

    response = sesh.patch("https://discord.com/api/v9/users/@me", json=payload, headers=headers)
    
    if response.status_code == 200:
        await ctx.send(f"```Successfully set display name to: {name}```")
    else:
        await ctx.send(f"```Failed to update display name: {response.status_code}```")       


@YLIN.command()
async def caption(ctx, *, text: str):
    await ctx.message.delete()
    if not ctx.message.attachments:
        return
    
    attachment = ctx.message.attachments[0]
    response = requests.get(attachment.url)
    img = Image.open(io.BytesIO(response.content))

    font = ImageFont.truetype("GGSANS_Semibold.ttf", 80)

    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    padding = 20
    new_img = Image.new("RGB", (img.width, img.height + text_h + padding), "white")
    new_img.paste(img, (0, text_h + padding))

    draw = ImageDraw.Draw(new_img)
    draw.text(((img.width - text_w) // 2, padding // 2), text, fill="black", font=font)

    img_bytes = io.BytesIO()
    new_img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    
    await ctx.send(file=discord.File(img_bytes, filename="YLIN.png"))
    os.remove("YLIN.png")


@YLIN.command()
async def ap2(ctx, *, message: str):
    global ap2
    if ap2:
        await ctx.message.delete()
        return

    ap2 = True
    await ctx.message.delete()
    await ap2task(ctx, message)

@YLIN.command(name="ap2e")
async def ap2e(ctx):
    global ap2
    ap2 = False
    await ctx.message.delete()


@YLIN.command()
async def vc(ctx, subcommand=None, *args):
    await ctx.message.delete()
    
    if subcommand is None:
        await ctx.send(
            "Voice Channel Commands:\n"
            "• `.vc join <channel_id> (guild_id)` - Join and stay in one voice channel\n"
            "• `.vc list (guild_id)` - List all available voice channels\n"
            "• `.vc leave (guild_id)` - Leave voice channel\n"
            "• `.vc status` - Show current VC status\n",
            delete_after=10
        )
        return

    if subcommand == "join":
        await vc_join(ctx, *args)
    elif subcommand == "list":
        await vc_list(ctx, *args)
    elif subcommand == "status":
        await vc_status(ctx)
    elif subcommand == "leave":
        await vc_leave(ctx, *args)
    else:
        await ctx.send("Invalid subcommand. Use `.vc` to see all available options.", delete_after=3)

async def vc_join(ctx, channel_id=None, guild_id=None):
    if not channel_id:
        await ctx.send("Please provide a voice channel ID", delete_after=3)
        return

    guild = YLIN.get_guild(int(guild_id)) if guild_id else ctx.guild
    if not guild:
        await ctx.send("Invalid guild ID", delete_after=3)
        return

    try:
        channel = guild.get_channel(int(channel_id))
        if not channel or not isinstance(channel, discord.VoiceChannel):
            await ctx.send("Invalid voice channel ID", delete_after=3)
            return

        voice_client = guild.voice_client
        if voice_client:
            await voice_client.move_to(channel)
        else:
            await channel.connect()
            
        await ctx.send(f"Connected to {channel.name}", delete_after=3)
    
    except Exception as e:
        await ctx.send(f"Error: {str(e)}", delete_after=3)

async def vc_list(ctx, guild_id=None):
    guild = YLIN.get_guild(int(guild_id)) if guild_id else ctx.guild
    if not guild:
        await ctx.send("Invalid guild ID", delete_after=3)
        return

    voice_channels = [f"{channel.name} : {channel.id}" for channel in guild.voice_channels]
    if voice_channels:
        await ctx.send("Available Voice Channels:\n" + "\n".join(voice_channels), delete_after=10)
    else:
        await ctx.send("No voice channels found.", delete_after=3)

async def vc_leave(ctx, guild_id=None):
    guild = YLIN.get_guild(int(guild_id)) if guild_id else ctx.guild
    if not guild:
        await ctx.send("Invalid guild ID", delete_after=3)
        return

    voice_client = guild.voice_client
    if voice_client:
        await voice_client.disconnect(force=True)
        await ctx.send("Left voice channel", delete_after=3)
    else:
        await ctx.send("Not in a voice channel", delete_after=3)


@YLIN.command()
async def cw(ctx, webhook_name: str):
    try:
        webhook = await ctx.channel.create_webhook(name=webhook_name)
        await ctx.send(f"Webhook created: {webhook.url}")
    except Exception as e:
        await ctx.send(f"Failed to create webhook: {e}")

@YLIN.command()
async def regionspam(ctx, channel_id: int):
    await ctx.message.delete()

    channel = YLIN.get_channel(channel_id)
    if not isinstance(channel, discord.VoiceChannel):
        await ctx.send("Invalid voice channel ID.")
        return

    rspam = False
    await ctx.send(f"Started region spam on: {channel.name}")

    while not rspam:
        try:
            r = random.choice(["us-west", "us-east", "us-central", "us-south", "rotterdam", "hongkong", "japan", "brazil", "singapore", "sydney", "russia", "india"])
            await channel.edit(rtc_region=r)
            await asyncio.sleep(10)
        except Exception as e:
            print(f"Error: {e}")
            break


@YLIN.command()
async def stopspamregion(ctx):
    await ctx.message.delete()

    rspam = True
    await ctx.send("Stopped all region spams", delete_after=3)


@YLIN.command()
async def lgcs(ctx):
    if not isinstance(ctx.channel, discord.DMChannel):
        return

    await ctx.message.delete()
    await ctx.send("Are you sure you want to leave all group DMs? Type 'yes' to confirm or 'no' to cancel.")

    def c(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['yes', 'no']

    try:
        r = await YLIN.wait_for('message', timeout=30.0, check=c)
    except asyncio.TimeoutError:
        return

    if r.content.lower() == 'no':
        return

    n = 0

    for g in YLIN.private_channels:
        if isinstance(g, discord.GroupChannel):
            try:
                async with aiohttp.ClientSession() as s:
                    u = f"https://discord.com/api/v9/channels/{g.id}"
                    h = {
                        "Authorization": token,
                        "Content-Type": "application/json",
                    }
                    async with s.delete(u, headers=h):
                        n += 1
                await asyncio.sleep(1)
            except:
                pass

    await ctx.send(f'left {n} gcs')
    

@YLIN.command()
async def ar(ctx, user: discord.User = None):
    global ar_active
    
    await ctx.message.delete()
    
    if user is None:
        if ar_active:
            ar_active = False
            ar_users.clear()
            await ctx.send('ar is now stopped for all users.', delete_after=5)
            savear()
        else:
            await ctx.send('ar is not running.', delete_after=5)
        return

    if not ar_active:
        ar_active = True

    if user.id in ar_users:
        ar_users.remove(user.id)
        if not ar_users:
            ar_active = False
        await ctx.send(f'Stopped ar for {user.name}.', delete_after=5)
    else:
        ar_users.add(user.id)
        await ctx.send(f'ar set for {user.name}.', delete_after=5)

    savear()
    await ctx.message.delete()


@YLIN.command()
async def arlist(ctx):
    loadar()

    if ar_users:
        user_list = [f"({user_id})" for user_id in ar_users]
        await ctx.send("ar enabled for the following users:\n" + "\n".join(user_list), delete_after=10)
    else:
        await ctx.send("No users have ar enabled", delete_after=5)
        

@YLIN.command()
async def purge(ctx, amount: int, channel_id: int = None):
    channel = YLIN.get_channel(channel_id) if channel_id else ctx.channel
    deleted = 0
    edited = 0
    cutoff = datetime.utcnow() - timedelta(days=14)

    async for message in channel.history(limit=None, oldest_first=False):
        if deleted + edited >= amount:
            break
        if message.author.id != YLIN.user.id:
            continue

        try:
            if message.created_at >= cutoff:
                await message.delete()
                deleted += 1
            else:
                await message.edit(content=".")
                edited += 1
            await asyncio.sleep(3)
        except Exception:
            continue

    await ctx.send(f"Deleted: {deleted} | Edited: {edited}", delete_after=5)

    
@YLIN.command()
async def status(ctx, type: str):
    await ctx.message.delete()
    type = type.lower()
    if type == 'on':
        await YLIN.change_presence(status=discord.Status.online)
        await ctx.send('Online.', delete_after=3)
    elif type == 'dnd':
        await YLIN.change_presence(status=discord.Status.dnd)
        await ctx.send('dnd', delete_after=3)        
    elif type == 'idle':
        await YLIN.change_presence(status=discord.Status.idle)
        await ctx.send('idle', delete_after=3)
    elif type == 'off':
        await YLIN.change_presence(status=discord.Status.invisible)
        await ctx.send('invisible', delete_after=3)
    else:
        await ctx.send('Invalid status type. Use `online` or `dnd` or `off` or `idle`.', delete_after=5)


@YLIN.command()
async def fs(ctx, times: int, *, message):
    await ctx.message.delete()
    
    for _ in range(times):
        try:
            await ctx.send(message)
        except discord.HTTPException as e:
            print(f'Error: {e}')
            await asyncio.sleep(5)
            

@YLIN.command()
async def lgc(ctx, channel_id: int = None):
	
    await ctx.message.delete()
    channel_id = channel_id or ctx.channel.id

    async with aiohttp.ClientSession() as session:
        url = f"https://discord.com/api/v9/channels/{channel_id}"
        headers = {
            "Authorization": token,
            "Content-Type": "application/json",
        }
        async with session.delete(url, headers=headers):
            pass


@YLIN.command()
async def rename(ctx, *, new_name: str):
    await ctx.message.delete()
    if isinstance(ctx.channel, (discord.TextChannel, discord.GroupChannel)):
        await ctx.channel.edit(name=new_name)


@YLIN.command()
async def rg(ctx, mode=None, *args):
    global rgid, rga
    await ctx.message.delete()

    if mode is None:
        await ctx.send("Usage: `.rg start (ids...) | stop | list | add <id...> | remove <id...>`", delete_after=5)
        return

    mode = mode.lower()

    if mode == "start":
        if rga:
            await ctx.send("Already rotating guilds.", delete_after=5)
            return

        rga = True
        rgid.clear()

        headers = {
            "authorization": token,
            "content-type": "application/json",
            "origin": "https://canary.discord.com",
            "referer": "https://canary.discord.com/channels/@me",
            "user-agent": "Mozilla/5.0",
        }

        if args:
            raw_ids = " ".join(args).replace(",", " ").split()
            rgid.extend([i for i in raw_ids if i.isdigit()])
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://canary.discord.com/api/v9/users/@me/guilds', headers=headers) as resp:
                    if resp.status != 200:
                        rga = False
                        await ctx.send("Failed to fetch guilds.", delete_after=5)
                        return

                    guilds = await resp.json()
                    for guild in guilds:
                        test_payload = {
                            'identity_guild_id': guild['id'],
                            'identity_enabled': True
                        }

                        async with session.put('https://canary.discord.com/api/v9/users/@me/clan', headers=headers, json=test_payload) as test_resp:
                            if test_resp.status == 200:
                                rgid.append(guild['id'])
                        await asyncio.sleep(0.12)

        if not rgid:
            rga = False
            await ctx.send("No valid guilds found for rotation.", delete_after=5)
            return

        await ctx.send(f"Rotating {len(rgid)} guild(s)...", delete_after=5)

        def change_identity(guild_id):
            try:
                response = requests.put(
                    "https://discord.com/api/v9/users/@me/clan",
                    headers={
                        "Authorization": token,
                        "Content-Type": "application/json"
                    },
                    json={
                        "identity_guild_id": guild_id,
                        "identity_enabled": True
                    }
                )
                if response.status_code != 200:
                    print(f"[!] Failed to switch to {guild_id} | {response.status_code} | {response.text}")
            except requests.RequestException as e:
                print(f"[!] Error: {e}")

        async def rotate_guilds():
            while rga:
                for gid in rgid:
                    if not rga:
                        break
                    change_identity(gid)
                    await asyncio.sleep(9)

        await rotate_guilds()

    elif mode == "stop":
        if rga:
            rga = False
            await ctx.send("Stopped rotating guilds.", delete_after=5)
        else:
            await ctx.send("No active rotation to stop.", delete_after=5)

    elif mode == "list":
        if not rgid:
            await ctx.send("No guilds in the rotation list.", delete_after=5)
            return

        headers = {
            "authorization": token,
            "content-type": "application/json"
        }

        guild_lines = []
        async with aiohttp.ClientSession() as session:
            for gid in rgid:
                async with session.get(f"https://discord.com/api/v9/users/@me/clan/guilds/{gid}", headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        tag = data.get("clan", {}).get("name", "No Tag")
                        guild_lines.append(f"`{gid}` | {tag}")
                    else:
                        guild_lines.append(f"`{gid}` | [Failed to fetch]")
                await asyncio.sleep(0.1)

        msg = "\n".join(guild_lines)
        await ctx.send(f"**Rotating {len(rgid)} guild(s):**\n{msg}", delete_after=15)

    elif mode == "add":
        new_ids = [i for i in args if i.isdigit()]
        added = 0
        for i in new_ids:
            if i not in rgid:
                rgid.append(i)
                added += 1
        await ctx.send(f"Added {added} guild(s) to rotation.", delete_after=5)

    elif mode == "remove":
        removed = 0
        for i in args:
            if i in rgid:
                rgid.remove(i)
                removed += 1
        await ctx.send(f"Removed {removed} guild(s) from rotation.", delete_after=5)

    else:
        await ctx.send("Unknown mode. Use: start, stop, list, add, remove", delete_after=5)


# ────────────────────────────────────────────────
#             AR1 COMMANDS
# ────────────────────────────────────────────────

@YLIN.command()
async def ar1(ctx, user: discord.User, *, message: str):
    global ar1_active
    await ctx.message.delete()

    if not message.strip():
        await ctx.send("You need to provide a reply message.", delete_after=6)
        return

    ar1_targets[user.id] = message
    ar1_active = True

    await ctx.send(f"**ar1** enabled for {user.mention}: will reply `{message}`", delete_after=8)


@YLIN.command(aliases=['sar1', 'ar1stop', 'ar1disable'])
async def stopar1(ctx):
    global ar1_active
    await ctx.message.delete()

    if not ar1_active:
        await ctx.send("ar1 is not active.", delete_after=6)
        return

    ar1_targets.clear()
    ar1_active = False
    await ctx.send("**ar1** stopped / disabled for all users.", delete_after=6)


@YLIN.command()
async def ar1list(ctx):
    await ctx.message.delete()

    if not ar1_active or not ar1_targets:
        await ctx.send("No users have ar1 enabled right now.", delete_after=6)
        return

    lines = []
    for uid, msg in ar1_targets.items():
        user = YLIN.get_user(uid)
        name = user.name if user else f"ID:{uid}"
        lines.append(f"{name} → `{msg}`")

    if not lines:
        await ctx.send("ar1 is active but no targets are set.", delete_after=6)
        return

    await ctx.send("**ar1 active for:**\n" + "\n".join(lines), delete_after=15)


main_template = [
    "this nigga was riding a [vehicle] with [name] in the passenger seat and he jumped out the door and turned into [adjective1] [object]",
    "nigga you used a [object] to kill a [insect] on the ground while you looked around searching for [adjective1] [seaanimal]",
    "nigga you threw [adjective1] [object] at [name] and you looked at the corner of your room and saw [name] butt booty naked getting [action] by [animename]",
    "nigga you and your [family] created a movie called the [number] [object]s that had [adjective1] [body]",
    "nigga you fell asleep on [location] and woke up to your penis getting tickled by [adjective1] [animals]",
    "nigga your [family] dropped their [food] down the stairs and they bent down trying to pick it up and then [name] popped out of nowhere and started twerking",
    "nigga your [race] [family] [action] [adjective1] [insect] while looking up and down having stick drift in your [body] and everytime you meet [name] you get excited and turn into [adjective1] [object]",
    "nigga you were caught [action] in a [location] while holding a [object] with [name]",
    "nigga you tried to cook [food] but ended up summoning [animename] in your [room]",
    "nigga you were found dancing with [animals] at the [event] dressed as a [adjective1] [object]",
    "nigga your [family] was seen playing [sport] with [name] at the [location] wearing [adjective1] [clothing]",
    "nigga you got into a fight with a [adjective1] [animal] while [action] and [name] recorded it",
    "nigga you transformed into a [adjective1] [mythicalcreature] after eating [food] given by [name]",
    "nigga you wrote a love letter to [name] and ended up getting chased by [insect]",
    "nigga you were singing [song] at the [event] when [animename] appeared and joined you",
    "nigga you tripped over a [object] while running from [animals] and fell into [location]",
    "nigga you were dreaming about [animename] and woke up covered in [food]",
    "nigga you and [name] went on an adventure to find the [adjective1] [object] but got lost in [location]",
    "nigga you were spotted riding a [vehicle] through the [location] with [adjective1] [animals]",
    "nigga your [family] decided to host a [event] in the [room] and invited [name] to join",
    "nigga you tried to impress [name] by [action] with a [object] but ended up embarrassing yourself",
    "nigga you and [name] got locked in a [room] with [adjective1] [animals] and had to find a way out",
    "nigga you participated in a [sport] match at the [event] and got cheered on by [animename]",
    "nigga you attempted to [action] in the [location] but got interrupted by [animals]",
    "nigga you discovered a hidden talent for [sport] while hanging out with [name] at the [location]",
    "nigga you found a [adjective1] [object] and decided to use it to prank [name] at the [event]",
    "nigga you got lost in the [location] while looking for [adjective1] [animals] and had to call [name] for help",
]

names = ["zirus", "yusky", "jason bourne", "huq", "ruin", "john wick", "mike wazowski", "thor", "spongebob", "patrick", "harry potter", "darth vader"]
adjectives = ["fluffy", "smelly", "huge", "tiny", "stinky", "bright", "dark", "slippery", "rough", "smooth"]
objects = ["rock", "pencil", "keyboard", "phone", "bottle", "book", "lamp", "balloon", "sock", "remote"]
insects = ["beetle", "cockroach", "dragonfly", "ant", "mosquito", "butterfly", "bee"]
seaanimals = ["dolphin", "octopus", "shark", "whale", "seal", "jellyfish", "crab"]
actions = ["kissing", "hugging", "fighting", "dancing", "singing", "running", "jumping", "crawling"]
animenames = ["itachi", "naruto", "goku", "luffy", "zoro", "sasuke", "vegeta"]
families = ["siblings", "cousins", "parents", "grandparents", "aunt", "uncle", "stepbrother", "stepsister"]
numbers = ["one", "two", "three", "four", "five", "six", "seven"]
bodies = ["head", "arm", "leg", "hand", "foot", "nose", "ear"]
locations = ["park", "beach", "library", "mall", "school", "stadium", "restaurant"]
animals = ["dog", "cat", "hamster", "elephant", "lion", "tiger", "bear", "giraffe"]
races = ["asian", "african", "caucasian", "hispanic", "native american", "martian"]
foods = ["pizza", "burger", "pasta", "taco", "sushi", "ice cream", "sandwich"]
events = ["concert", "festival", "wedding", "party", "ceremony"]
sports = ["soccer", "basketball", "baseball", "tennis", "cricket"]
clothing = ["shirt", "pants", "hat", "shoes", "jacket"]
mythicalcreatures = ["dragon", "unicorn", "phoenix", "griffin", "centaur"]
songs = ["despacito", "baby shark", "old town road", "shape of you", "bohemian rhapsody"]
vehicles = ["bike", "car", "scooter", "skateboard", "bus", "train", "airplane", "boat"]
rooms = ["living room", "bedroom", "kitchen", "bathroom", "attic", "basement", "garage"]

def replace_placeholders(template):
    template = template.replace("[name]", random.choice(names))
    template = template.replace("[adjective1]", random.choice(adjectives))
    template = template.replace("[object]", random.choice(objects))
    template = template.replace("[insect]", random.choice(insects))
    template = template.replace("[seaanimal]", random.choice(seaanimals))
    template = template.replace("[action]", random.choice(actions))
    template = template.replace("[animename]", random.choice(animenames))
    template = template.replace("[family]", random.choice(families))
    template = template.replace("[number]", random.choice(numbers))
    template = template.replace("[body]", random.choice(bodies))
    template = template.replace("[location]", random.choice(locations))
    template = template.replace("[animals]", random.choice(animals))
    template = template.replace("[race]", random.choice(races))
    template = template.replace("[food]", random.choice(foods))
    template = template.replace("[event]", random.choice(events))
    template = template.replace("[sport]", random.choice(sports))
    template = template.replace("[clothing]", random.choice(clothing))
    template = template.replace("[mythicalcreature]", random.choice(mythicalcreatures))
    template = template.replace("[song]", random.choice(songs))
    template = template.replace("[vehicle]", random.choice(vehicles))
    template = template.replace("[room]", random.choice(rooms))
    template = template.replace("[animal]", random.choice(animals))
    return template

def generate_pack():
    template = random.choice(main_template)
    pack = replace_placeholders(template)
    return pack


@YLIN.command()
async def packgen(ctx):
    await ctx.message.delete()
    pack = generate_pack()
    await ctx.send(pack)


@YLIN.command()
async def ping(ctx):
    def convert_units(value):
        units = ["ps", "ns", "µs", "ms", "s"]
        scales = [1e-12, 1e-9, 1e-6, 1e-3, 1]  
        for i in range(len(scales) - 1, -1, -1):
            if value >= scales[i] or i == 0:
                return f"{value / scales[i]:.2f}{units[i]}"

    start_determinism = time.perf_counter()
    _ = ctx.prefix
    end_determinism = time.perf_counter()
    prefix_determinism_time = end_determinism - start_determinism  

    host = YLIN.latency
    api = (datetime.now(timezone.utc) - ctx.message.created_at.replace(tzinfo=timezone.utc)).total_seconds()
    now = datetime.now(timezone.utc)
    uptime_duration = now - start_time

    d = uptime_duration.days
    h, r = divmod(uptime_duration.seconds, 3600)
    m, s = divmod(r, 60)

    upart = []
    if d > 0:
        upart.append(f"{d}d")
    if h > 0:
        upart.append(f"{h}h")
    if m > 0:
        upart.append(f"{m}m")
    if s > 0 or not upart:
        upart.append(f"{s}s")

    uptime = " ".join(upart)

    response = (
        "```\n"
        "~ TYLIN Ping\n"
        "``````js\n"
        f"Prefix: <{convert_units(prefix_determinism_time)}>\n"
        f"Latency: <{convert_units(host)}>\n"
        f"API: <{convert_units(api)}>\n"
        f"Uptime: <{uptime}>\n"
        "```"
    )
    
    await ctx.send(response)


# ────────────────────────────────────────────────
#             CHATPACK – FIXED CUSTOM DELAY + 1.6s DEFAULT
# ────────────────────────────────────────────────

chatpack_task = None
chatpack_channel = None
chatpack_target_user = None
chatpack_base_delay = 1.6  # default when no custom delay is given


@YLIN.command(name="chatpack")
async def chatpack(ctx, *args):
    global chatpack_task, chatpack_channel, chatpack_target_user, chatpack_base_delay

    await ctx.message.delete()

    if chatpack_task is not None and not chatpack_task.done():
        return

    member = None
    custom_delay = None

    for arg in args:
        if '<@' in arg or arg.startswith('@'):
            try:
                member = await commands.MemberConverter().convert(ctx, arg)
                continue
            except:
                pass

        try:
            delay_val = float(arg)
            if delay_val > 0:
                custom_delay = delay_val
        except ValueError:
            pass

    if custom_delay is not None:
        chatpack_base_delay = custom_delay
    else:
        chatpack_base_delay = 1.6

    try:
        with open("chatpack.txt", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
    except Exception:
        return

    if not lines:
        return

    chatpack_channel = ctx.channel
    chatpack_target_user = member.id if member else None

    variation = max(0.6, chatpack_base_delay * 0.4)
    min_d = max(0.7, chatpack_base_delay - variation)
    max_d = chatpack_base_delay + variation

    async def chatpack_loop():
        i = 0
        while True:
            try:
                if chatpack_target_user is None:
                    await chatpack_channel.send(lines[i % len(lines)])
                    i += 1
                    await asyncio.sleep(random.uniform(min_d, max_d))
                else:
                    await asyncio.sleep(8)
            except Exception:
                await asyncio.sleep(4)

    chatpack_task = YLIN.loop.create_task(chatpack_loop())


@YLIN.command(name="stopchatpack")
async def stopchatpack(ctx):
    global chatpack_task, chatpack_channel, chatpack_target_user, chatpack_base_delay

    await ctx.message.delete()

    if chatpack_task is None or chatpack_task.done():
        return

    chatpack_task.cancel()
    chatpack_task = None
    chatpack_channel = None
    chatpack_target_user = None
    chatpack_base_delay = 1.6


YLIN.loop.create_task(artask())
YLIN.loop.create_task(reacttask())

YLIN.run(token, bot=False, reconnect=True)
