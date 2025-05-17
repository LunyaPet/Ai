import asyncio
import random
import re

import discord
import sentry_sdk

from constants import GUILD


def handle_colon_three(message: discord.Message):
    # count :3 in message
    count = 0
    for i in re.finditer(r":(3+)", message.content.lower()):
        count = count + len(i[1])

    if count == 0:
        return ""

    return ":3 " * count

def generate_meow():
    meow = random.choice(["meow", "nya", "mraow", "mwrmmwra"])

    if meow == "nya":
        return "ny" + random.randint(1, 8) * "a"
    elif meow == "mwrmmwra":
        meow = "mr"
        for i in range(random.randint(4, 12)):
            meow += random.choice(["a", "w", "r"])

        return meow

    return meow


def handle_meow(message: discord.Message):
    # count meows
    count = len(re.findall(r"(m[mraeow]{3,}|nya+)", message.content.lower()))

    if count == 0:
        return ""

    return " ".join([generate_meow() for _ in range(count)]) + " :3"


def handle_owo(message: discord.Message):
    # count OwOs and UwUs
    count = len(re.findall(r"([ou>]w[<ou])", message.content.lower()))

    if count == 0:
        return ""

    return " ".join(random.choices(["OwO", "owo", "UwU", "uwu", ">w<"], k=count)) + " :3"


def handle_gex(message: discord.Message):
    count_say_gex = len(re.findall(r"say gex", message.content.lower()))
    count_sesbian_lex = len(re.findall(r"sesbian lex", message.content.lower()))

    resp = "say gex " * count_say_gex
    resp += "sesbian lex " * count_sesbian_lex
    return resp.strip()


class FunnyAutoResponse(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.Cog.listener()
    async def on_message(self, message: discord.Message):
        try:
            if message.author.bot:
                return

            if message.guild.id != int(GUILD):
                return

            if "so true" in message.content or "so real" in message.content:
                await message.reply(file=discord.File("rom/sotruebestie.gif"))

            message_reply = " ".join([
                handle_meow(message),
                handle_colon_three(message),
                handle_owo(message),
                handle_gex(message)
            ])

            message_reply = message_reply.replace("  ", " ")

            if len(message_reply.strip()) > 0:
                await message.channel.send(message_reply)
        except Exception as e:
            sentry_sdk.capture_exception(e)
