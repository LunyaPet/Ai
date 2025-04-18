import os

import discord
import sentry_sdk

from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration

from cogs.dev_commands import DevCommands
from cogs.test_user import UserCommands
from cogs.verification import Verification
from constants import DISCORD_TOKEN

sentry_sdk.init("https://cb9c3c0bc7a849c6bca64c6b82f2707d@glitchtip.mldchan.dev/23",
                integrations=[AioHttpIntegration(), AsyncioIntegration()], traces_sample_rate=1.0,
                profiles_sample_rate=1.0)

bot = discord.Bot(intents=discord.Intents.all())


@bot.event
async def on_ready():
    print(f"{bot.user.display_name} has connected to Discord!")


bot.add_cog(DevCommands(bot))
bot.add_cog(Verification(bot))
bot.add_cog(UserCommands(bot))

bot.run(DISCORD_TOKEN)
