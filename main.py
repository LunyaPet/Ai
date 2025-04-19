import os

import discord
import sentry_sdk

from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration

from cogs.auto_fedi_notifs import AutoFediNotifications
from cogs.auto_tiktok_notifs import AutoTikTokNotifications
from cogs.auto_yt_notifs import AutoYouTubeNotifications
from cogs.dev_commands import DevCommands
from cogs.user_commands import UserCommands
from cogs.verification import Verification
from constants import DISCORD_TOKEN, SENTRY_DSN

sentry_sdk.init(SENTRY_DSN,
                integrations=[AioHttpIntegration(), AsyncioIntegration()], traces_sample_rate=1.0,
                profiles_sample_rate=1.0)

bot = discord.Bot(intents=discord.Intents.all())


@bot.event
async def on_ready():
    print(f"{bot.user.display_name} has connected to Discord!")


bot.add_cog(DevCommands(bot))
bot.add_cog(Verification(bot))
bot.add_cog(UserCommands(bot))
bot.add_cog(AutoFediNotifications(bot))
bot.add_cog(AutoYouTubeNotifications(bot))
bot.add_cog(AutoTikTokNotifications(bot))

bot.run(DISCORD_TOKEN)
