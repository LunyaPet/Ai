import asyncio

import discord

from cogs.verification import StartVerificationButton


class DevCommands(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.Cog.listener()
    async def on_ready(self):
        print("Dev Commands Cog is ready!")

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
