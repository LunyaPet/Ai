import asyncio

import discord

from cogs.verification import StartVerificationButton
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
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType[status_data["mode"]], status=status_data["status"]))

    dev_group = discord.SlashCommandGroup(name="dev", description="Developer commands", guild_ids=[1362400131206348930],
        default_member_permissions=discord.Permissions(administrator=True), )

    @dev_group.command(name="debug")
    async def debug_cmd(self, ctx: discord.ApplicationContext):
        await ctx.respond("Debug command", ephemeral=True)

    @dev_group.command(name="send_verify_message")
    async def send_verify_cmd(self, ctx: discord.ApplicationContext):
        await asyncio.gather(ctx.channel.send(
            "# Verify\nIn order to access the rest of this server, you must verify. Please click the \"start verify\" button in order to begin!",
            view=StartVerificationButton()), ctx.respond("Sent", ephemeral=True))

    @dev_group.command(name="set_status")
    @discord.option(name="mode", description="The mode to set the status to", type=str, choices=["watching", "streaming", "playing", "competing", "listening"])
    async def set_status(self, ctx: discord.ApplicationContext, mode: str, status: str):
        existing_data = get_data("status")
        existing_data["mode"] = mode
        existing_data["status"] = status
        set_data("status", existing_data)

        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType[mode], status=status))
        await ctx.respond(f"Status set to {mode}: {status}!", ephemeral=True)
