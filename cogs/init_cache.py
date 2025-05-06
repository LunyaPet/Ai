import asyncio

import discord
import sentry_sdk
from discord import CategoryChannel

from constants import GUILD


class InitCache(discord.Cog):
    def __init__(self, bot: discord.Bot):
        super().__init__()
        self.bot = bot

    async def init_channel(self, channel: discord.TextChannel):
        try:
            a = await channel.history(limit=None).flatten()
            print(f"[InitCache]#{channel.name} has been init with {len(a)} message!!!", flush=True)
        except Exception as e:
            print(f"[InitCache]#{channel.name} failed with {e=}", flush=True)
            sentry_sdk.capture_exception(e)

    @discord.Cog.listener()
    async def on_ready(self):
        print("[InitCache]Init cache", flush=True)
        try:
            guild = self.bot.get_guild(int(GUILD))

            if guild is None:
                return

            # Init channels
            await asyncio.gather(*[self.init_channel(i) for i in guild.channels if not isinstance(i, CategoryChannel)])
        except Exception as e:
            sentry_sdk.capture_exception(e)
            print("[InitCache]Init error", flush=True)

