import random
import re

import discord
import sentry_sdk

from constants import GUILD


async def handle_colon_three(message: discord.Message):
    # count :3 in message
    count = 0
    for i in re.finditer(r":(3+)", message.content):
        count = count + len(i[1])

    if count == 0:
        return

    await message.channel.send(":3 " * count)

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


async def handle_meow(message: discord.Message):
    # count meows
    count = len(re.findall(r"(m[raow]+|nya+)", message.content))

    if count == 0:
        return

    await message.channel.send(" ".join([generate_meow() for _ in range(count)]) + " :3")


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

            # :3
            await handle_colon_three(message)

            # meow
            await handle_meow(message)
        except Exception as e:
            sentry_sdk.capture_exception(e)
