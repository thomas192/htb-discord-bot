import asyncio
import os
import discord
from datetime import datetime
from discord.ext import commands
from discord.ext import tasks
from dotenv import load_dotenv
from htb import update_active_machines, update_machines_activity, get_active_machines
from utils import load_from_json, write_to_json

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

init_cpt = 0
channel = None


# creates a pawn alert embed
def create_embed(username, machine_name, difficulty, type, img_url):
    description = f"  |  `{username}` pawned **{machine_name}**\n" \
                  f"  |  difficulty: *{difficulty}*\n" \
                  f"  |  type: *{type}*"
    embed = discord.Embed(title="☠️      **PAWN ALERT**      ☠️",
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
    # check if htb_id is not already set for another user
    for user in dict:
        if htb_id == dict[user]["htb_id"]:
            await ctx.send(f"HTB id {htb_id} is already set for another user")
            return
    # if id is already set
    if discord_id in dict:
        await ctx.send(f"You are already bound")
        return
    # if id is not set
    else:
        dict[discord_id] = {"htb_id": htb_id, "avatar_url": ctx.message.author.avatar.url, "f_user": [], "f_root": []}
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


@tasks.loop(minutes=1)
async def check_for_new_flags():
    print(f"check_for_new_flags() at {datetime.now()}")
    global channel

    update_active_machines_non_blocking = asyncio.to_thread(update_active_machines)
    await update_active_machines_non_blocking
    update_machines_activity_non_blocking = asyncio.to_thread(update_machines_activity)
    await update_machines_activity_non_blocking

    dict = load_from_json("dict.json")
    machine_list = get_active_machines()
    for m in machine_list:
        print(f"[*] checking machine activity {m[0]}")
        m_id = m[0]
        m_name = m[1]
        m_difficulty = m[2]
        machine = load_from_json("machines_activity_" + m[0] + ".json")
        for activity in machine["activity"]:
            type = activity["type"]
            htb_id = str(activity["user_id"])
            u_name = activity["user_name"]
            if type == "root" or type == "user":
                for user in dict:
                    # if user flagged
                    if htb_id == dict[user]["htb_id"]:
                        print(f"htb_id {htb_id} flagged {type} machine {m_id}")
                        # if flag has not been accounted for
                        if m_id not in dict[user]["f_" + type]:
                            print("flag not accounted for")
                            # update dict
                            dict[user]["f_" + type].append(m_id)
                            embed = create_embed(username=u_name,
                                                 machine_name=m_name,
                                                 difficulty=m_difficulty,
                                                 type=type,
                                                 img_url=dict[user]["avatar_url"])
                            await channel.send(embed=embed)

    write_to_json("dict.json", dict)


# !manual_flag 1239115 DeVr0S Photobomb 500 user Easy
@bot.command(name="manual_flag")
async def bind(ctx,
               htb_id: str,
               u_name: str,
               m_name: str,
               machine_id: str,
               type: str,
               m_difficulty: str):
    global channel

    dict = load_from_json("dict.json")
    for user in dict:
        if dict[user]["htb_id"] == htb_id:
            # update dict
            dict[user]["f_" + type].append(machine_id)
            # send alert
            embed = create_embed(username=u_name,
                                 machine_name=m_name,
                                 difficulty=m_difficulty,
                                 type=type,
                                 img_url=dict[user]["avatar_url"])
            await channel.send(embed=embed)
            break

    write_to_json("dict.json", dict)


bot.run(TOKEN)
