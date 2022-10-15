import os
import json
import discord
from discord.ext import commands
from discord.ext import tasks
from dotenv import load_dotenv
from htb import update_active_machines, update_machines_activity, get_active_machines

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

init_cpt = 0
channel = None


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user.name}")


@bot.command(name="bind")
async def bind(ctx, htb_id: str):
    global dict
    discord_id = str(ctx.author.id)
    # load dict from file
    with open("dict.json", "r") as f:
        dict = json.load(f)
    # check if htb_id is not already set for another user
    for user in dict:
        if htb_id == dict[user]["htb_id"]:
            await ctx.send(f"HTB id {htb_id} is already set for another user")
            return
    # if id is already set
    if discord_id in dict:
        await ctx.send(f"Your discord id is already bound to HTB id {discord_id}")
        return
    # if id is not set
    else:
        dict[discord_id] = {"htb_id": htb_id, "avatar_url": ctx.message.author.avatar.url, "f_user": [], "f_root": []}
        await ctx.send(f"Your discord id is now bound to HTB id {htb_id}")
    # update dict
    with open("dict.json", "w") as f:
        json.dump(dict, f)


@bot.command(name="purge")
async def purge(ctx):
    global dict
    discord_id = str(ctx.author.id)
    # load dict from file
    with open("dict.json", "r") as f:
        dict = json.load(f)
    if discord_id in dict:  # if id is already set
        purged_id = dict[discord_id]["htb_id"]
        dict.pop(discord_id)     # remove entry
        await ctx.send(f"Your discord id is no longer bound to HTB id {purged_id}")
    else:   # if id is not set
        await ctx.send("Your discord id is not bound to any HTB id")
        return
    # update dict
    with open("dict.json", "w") as f:
        json.dump(dict, f)


@bot.command(name="init")
async def init(ctx):
    global channel
    global init_cpt
    if init_cpt < 1:
        channel = discord.utils.get(ctx.guild.channels, name="pwned")
        check_for_new_flags.start()
        init_cpt += 1
        await channel.send("Initialisation done")
    else:
        await channel.send("I cannot be initialised more than once")


@tasks.loop(minutes=3)
async def check_for_new_flags():
    print("check_for_new_flags()")
    global dict
    global channel
    update_active_machines()
    update_machines_activity()
    # load dict from file
    with open("dict.json", "r") as f:
        dict = json.load(f)
    machine_list = get_active_machines()
    # iterate over active machines
    for m in machine_list:
        filename = "machines_activity_" + m[0] + ".json"
        m_id = m[0]
        m_name = m[1]
        m_difficulty = m[2]
        with open(filename) as f:
            machines = json.load(f)
            # iterate over each machine's activity
            for a in machines["activity"]:
                type = a["type"]
                htb_id = str(a["user_id"])
                u_name = a["user_name"]
                # if local user got flag
                if type == "root" or type == "user":
                    for user in dict:
                        # if user flagged
                        if htb_id == dict[user]["htb_id"]:
                            print(f"htb_id {htb_id} flagged {type} machine {m_id}")
                            # if flag has not been accounted for
                            if m_id not in dict[user]["f_"+type]:
                                print("flag not accounted for")
                                dict[user]["f_"+type].append(m_id)
                                # send alert
                                description = f"  |  `{u_name}` pawned **{m_name}**\n"\
                                              f"  |  difficulty: *{m_difficulty}*\n"\
                                              f"  |  type: *{type}*"
                                embed = discord.Embed(title="☠️      **PAWN ALERT**      ☠️",
                                                      description=description)
                                embed.set_thumbnail(url=dict[user]["avatar_url"])
                                await channel.send(embed=embed)
    # update dict
    with open("dict.json", "w") as f:
        json.dump(dict, f)

bot.run(TOKEN)
