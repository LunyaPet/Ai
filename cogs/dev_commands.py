import discord
import sentry_sdk

from constants import OWNER, GUILD
from util.storage import get_data, set_data


class DevCommands(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.Cog.listener()
    async def on_ready(self):
        print("Dev Commands Cog is ready!")

        # Set status if in configuration file
        status_data = get_data("status")
        if "mode" in status_data and "status" in status_data:
            activity_type = discord.ActivityType.playing
            if status_data["mode"] == "watching":
                activity_type = discord.ActivityType.watching
            elif status_data["mode"] == "streaming":
                activity_type = discord.ActivityType.streaming
            elif status_data["mode"] == "competing":
                activity_type = discord.ActivityType.competing
            elif status_data["mode"] == "listening":
                activity_type = discord.ActivityType.listening

            activity = discord.Activity(
                type=activity_type,
                name=status_data["status"]
            )

            await self.bot.change_presence(activity=activity)

    dev_group = discord.SlashCommandGroup(name="dev", description="Developer commands", guild_ids=[int(GUILD)],
        default_member_permissions=discord.Permissions(administrator=True), )

    @dev_group.command(name="debug")
    async def debug_cmd(self, ctx: discord.ApplicationContext):
        await ctx.respond("Debug command", ephemeral=True)

    @dev_group.command(name="set_status")
    @discord.option(name="mode", description="The mode to set the status to", type=str, choices=["watching", "streaming", "playing", "competing", "listening"])
    async def set_status(self, ctx: discord.ApplicationContext, mode: str, status: str):
        try:
            if ctx.user.id != int(OWNER):
                await ctx.respond("You are not authorized to use this command!", ephemeral=True)
                return

            existing_data = get_data("status")
            existing_data["mode"] = mode
            existing_data["status"] = status
            set_data("status", existing_data)

            activity_type = discord.ActivityType.playing
            if mode == "watching":
                activity_type = discord.ActivityType.watching
            elif mode == "streaming":
                activity_type = discord.ActivityType.streaming
            elif mode == "competing":
                activity_type = discord.ActivityType.competing
            elif mode == "listening":
                activity_type = discord.ActivityType.listening

            activity = discord.Activity(
                type=activity_type,
                name=status
            )

            await self.bot.change_presence(activity=activity)
            await ctx.respond(f"Status set to {mode}: {status}!", ephemeral=True)
        except Exception as e:
            sentry_sdk.capture_exception(e)
