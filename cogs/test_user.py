import discord
import sentry_sdk
import subprocess

from constants import OWNER


class MeowComponent(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Meow", style=discord.ButtonStyle.primary)
    async def meow(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("Meow~! :3", ephemeral=True)

class UserCommands(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.command(name='ping', description='Tests connection to Discord', integration_types=[discord.IntegrationType.user_install])
    async def ping(self, ctx: discord.ApplicationContext):
        await ctx.respond(f'Pong! {self.bot.latency * 1500} ms', ephemeral=(ctx.user.id != int(OWNER)))

    @discord.command(name='message', description='Send message as bot', integration_types=[discord.IntegrationType.user_install])
    async def ping(self, ctx: discord.ApplicationContext, msg: str):
        if ctx.user.id != int(OWNER):
            await ctx.respond("You are not authorized to use this command!", ephemeral=True)
            return

        await ctx.respond(msg)

    @discord.command(name="information", description="Print information about the server", integration_types=[discord.IntegrationType.user_install])
    async def information(self, ctx: discord.ApplicationContext):
        try:
            if ctx.user.id != int(OWNER):
                await ctx.respond("You are not authorized to use this command!", ephemeral=True)
                return

            uname = subprocess.run(["uname", "-a"], capture_output=True, text=True)
            uptime = subprocess.run(["uptime"], capture_output=True, text=True)

            await ctx.respond("-# " + uname.stdout + "\n-# " + uptime.stdout)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await ctx.respond("An error occurred while executing the command.", ephemeral=True)

    @discord.command(name="meow", description="meow", integration_types=[discord.IntegrationType.user_install])
    async def meow(self, ctx: discord.ApplicationContext):
        if ctx.user.id != int(OWNER):
            await ctx.respond("You are not authorized to use this command!", ephemeral=True)
            return

        await ctx.respond("meow", view=MeowComponent())
