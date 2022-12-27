import asyncio
import os
import discord
from datetime import datetime
from discord.ext import commands
from discord.ext import tasks
from dotenv import load_dotenv
from htb import update_active, update_activity, get_active
from utils import load_from_json, write_to_json

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

init_cpt = 0
channel = None


def create_embed(username, name, difficulty, a_type, f_type, img_url):
    description = f"  |  `{username}` pawned {a_type} **{name}**\n" \
                  f"  |  difficulty: *{difficulty}*\n" \
                  f"  |  type: *{f_type}*" if f_type else ""
    embed = discord.Embed(title="☠️             **PAWN ALERT**             ☠️",
                          description=description)
    embed.set_thumbnail(url=img_url)
    return embed


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user.name}")


@bot.command(name="bind")
async def bind(ctx, htb_id: str):
    discord_id = str(ctx.author.id)
    dict = load_from_json("dict.json")
    for user in dict:
        if htb_id == dict[user]["htb_id"]:
            await ctx.send(f"HTB id {htb_id} is already set for another user")
            return
    if discord_id in dict:
        await ctx.send(f"You are already bound")
        return
    else:
        dict[discord_id] = {"htb_id": htb_id, "avatar_url": ctx.message.author.avatar.url, "machine_blood": [],
                            "machine_user": [], "machine_root": [], "challenge_blood": [], "challenge_own": []}
        await ctx.send(f"Your discord id is now bound to HTB id {htb_id}")

    write_to_json("dict.json", dict)


@bot.command(name="purge")
async def purge(ctx):
    discord_id = str(ctx.author.id)
    dict = load_from_json("dict.json")
    if discord_id in dict:  # if id is already set
        purged_id = dict[discord_id]["htb_id"]
        dict.pop(discord_id)  # remove entry
        await ctx.send(f"Your discord id is no longer bound to HTB id {purged_id}")
    else:  # if id is not set
        await ctx.send("Your discord id is not bound to any HTB id")
        return

    write_to_json("dict.json", dict)


@bot.command(name="init")
async def init(ctx):
    global channel
    global init_cpt
    if init_cpt < 1:
        channel = discord.utils.get(ctx.guild.channels, name="pwned")
        check_for_new_flags.start()
        init_cpt += 1
        await channel.send("Initialization done")
    else:
        await channel.send("I cannot be initialized more than once")


@tasks.loop(minutes=12)
async def check_for_new_flags():
    print(f"check_for_new_flags() at {datetime.now()}")
    global channel
    await asyncio.to_thread(update_active, machines=True, challenges=True)
    await asyncio.to_thread(update_activity, machines=True, challenges=True)
    dict = load_from_json("dict.json")
    actives = get_active(machines=True, challenges=True)
    for active in actives:
        a_id = active["id"]
        a_type = active["type"]
        print(f"[*] checking {a_type} activity {a_id}")
        activities = load_from_json(f"{a_type}/{a_id}.json") if a_type in ["machine", "challenge"] else None
        # Sometimes the api returns "Too many requests"
        try:
            flags = activities["info"]["activity"]
        except KeyError as e:
            print(f"KeyError {e}")
            continue
        for flag in flags:
            f_htb_id = str(flag["user_id"])
            f_type = flag["type"]
            for user in dict:
                if dict[user]["htb_id"] == f_htb_id:
                    print(f"htb_id {f_htb_id} flagged {a_type} {a_id}")
                    f_type_dict = {"machine": ["blood", "user", "root"], "challenge": ["blood", "own"]}
                    if a_type in ["machine", "challenge"]:
                        if f_type in f_type_dict[a_type] and a_id not in dict[user][a_type + "_" + f_type]:
                            print("flag not accounted for")
                            dict[user][a_type + "_" + f_type].append(a_id)
                            embed = create_embed(username=flag["user_name"],
                                                 name=active["name"],
                                                 difficulty=active["difficulty"],
                                                 a_type=a_type,
                                                 f_type=f_type,
                                                 img_url=dict[user]["avatar_url"])
                            await channel.send(embed=embed)
    write_to_json("dict.json", dict)


# !manual_flag 1020657 0xK2 Photobomb 500 machine user Easy
@bot.command(name="manual_flag")
async def manual_flag(ctx,
                      htb_id: str,
                      username: str,
                      a_name: str,
                      a_id: str,
                      a_type: str,
                      f_type: str,
                      difficulty: str):
    global channel
    dict = load_from_json("dict.json")
    for user in dict:
        if dict[user]["htb_id"] == htb_id:
            dict[user][a_type + "_" + f_type].append(a_id)
            embed = create_embed(username=username,
                                 name=a_name,
                                 difficulty=difficulty,
                                 a_type=a_type,
                                 f_type=f_type,
                                 img_url=dict[user]["avatar_url"])
            await channel.send(embed=embed)
            break

    write_to_json("dict.json", dict)


bot.run(TOKEN)
