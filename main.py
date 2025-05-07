import os

import discord
import sentry_sdk
from discord.ext import commands

from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration

from cogs.auto_fedi_notifs import AutoFediNotifications
from cogs.auto_tiktok_notifs import AutoTikTokNotifications
from cogs.auto_yt_notifs import AutoYouTubeNotifications
from cogs.dev_commands import DevCommands
from cogs.funny_auto_response import FunnyAutoResponse
from cogs.general_cleaner import GeneralCleaner
from cogs.init_cache import InitCache
from cogs.media_threads import MediaThreads
from cogs.message_reporting import MessageReporting
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

@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error):
    if isinstance(error, commands.CommandOnCooldown):
        minutes = int(error.retry_after / 60)
        seconds = int(error.retry_after % 60)
        if minutes > 0:
            await ctx.respond(
                f"Cooldown! {minutes} minutes and {seconds} seconds remaining :3",
                ephemeral=True)
        else:
            await ctx.respond(f"Cooldown! {seconds} seconds remaining :3", ephemeral=True)
        return

    if isinstance(error, commands.MissingPermissions):
        await ctx.respond(f"Missing permissions UwU!\nThese are missing: {', '.join(error.missing_permissions)}",
            ephemeral=True)
        return

    if isinstance(error, commands.NoPrivateMessage):
        await ctx.respond("This command was only meant for servers... :(", ephemeral=True)
        return

    if isinstance(error, commands.BotMissingPermissions):
        await ctx.respond(f"Sowwie mldchan gave too little permissions to me :( ask her to give me {', '.join(error.missing_permissions)} 🥺",
            ephemeral=True)
        return

    if isinstance(error, commands.PrivateMessageOnly):
        await ctx.respond("This command was only meant to be used in DM's with me 👉👈", ephemeral=True)
        return

    sentry_sdk.capture_exception(error)
    try:
        # respond
        await ctx.respond("An error occured with this command, please ask mldchan to fix it :(", ephemeral=True)
    except Exception as e:
        sentry_sdk.capture_exception(e)
    raise error

bot.add_cog(DevCommands(bot))
bot.add_cog(Verification(bot))
bot.add_cog(UserCommands(bot))
bot.add_cog(AutoFediNotifications(bot))
bot.add_cog(AutoYouTubeNotifications(bot))
bot.add_cog(AutoTikTokNotifications(bot))
bot.add_cog(MessageReporting(bot))
bot.add_cog(GeneralCleaner(bot))
bot.add_cog(MediaThreads(bot))
bot.add_cog(FunnyAutoResponse(bot))
bot.add_cog(InitCache(bot))

bot.run(DISCORD_TOKEN)
