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

            for i in guild.text_channels:
                asyncio.get_running_loop().create_task(self.init_channel(i), name=f"InitCache Text Channel #{i.name} ({i.id})")

            print(f"[InitCache]Created {len(guild.text_channels)} tasks")

            print("[InitCache]Init cache", flush=True)
            print("[InitCache]Init DM cache", flush=True)
            # DM channels
            for i in self.bot.private_channels:
                asyncio.get_running_loop().create_task(self.init_channel(i), name=f"InitCache Private Channel {i.id}")
            print(f"[InitCache]Created {len(self.bot.private_channels)} tasks")
            print("[InitCache]Init DM cache done..", flush=True)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            print("[InitCache]Init error", flush=True)

