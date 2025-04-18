import random
from idlelib.window import add_windows_to_menu

import discord
import sentry_sdk
import subprocess

from discord import Interaction

from constants import OWNER


class MeowComponent(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Meow", style=discord.ButtonStyle.primary)
    async def meow(self, button: discord.ui.Button, interaction: discord.Interaction):
        meows = ["Mraow~", "meow :3", "mwmrwmrma~ :3 ", "mwrmwmrwma :3", "mwrmwma :3", "meow", "mmrwwa uwu :3"]
        await interaction.response.send_message(random.choice(meows))

class SillyModal(discord.ui.Modal):
    def __init__(self, title: str, label: str, placeholder: str):
        super().__init__(title=title)

        self.label = discord.ui.InputText(
            label=label,
            placeholder=placeholder,
            style=discord.InputTextStyle.short
        )

        self.add_item(self.label)

    async def callback(self, interaction: Interaction):
        await interaction.respond(f"{interaction.user.mention}: {self.label.value} :3")


class SillyComponent(discord.ui.View):
    def __init__(self, title: str, label: str, placeholder: str):
        super().__init__()
        self.title = title
        self.label = label
        self.placeholder = placeholder

    @discord.ui.button(label=":3", style=discord.ButtonStyle.primary)
    async def silly(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(SillyModal(self.title, self.label, self.placeholder))

class UserCommands(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.command(name='ping', description='Tests connection to Discord', integration_types=[discord.IntegrationType.user_install])
    async def ping(self, ctx: discord.ApplicationContext):
        await ctx.respond(f'Pong! {self.bot.latency * 1500} ms', ephemeral=(ctx.user.id != int(OWNER)))

    @discord.command(name='message', description='Send message as bot', integration_types=[discord.IntegrationType.user_install])
    async def message(self, ctx: discord.ApplicationContext, msg: str):
        if ctx.user.id != int(OWNER):
            await ctx.respond("You are not authorized to use this command!", ephemeral=True)
            return

        await ctx.respond(msg)

    @discord.command(name="information", description="Print information about the server", integration_types=[discord.IntegrationType.user_install])
    async def information(self, ctx: discord.ApplicationContext, public: bool = False):
        try:
            if ctx.user.id != int(OWNER):
                await ctx.respond("You are not authorized to use this command!", ephemeral=True)
                return

            uname = subprocess.run(["uname", "-a"], capture_output=True, text=True)
            uptime = subprocess.run(["uptime"], capture_output=True, text=True)

            await ctx.respond(uname.stdout + "\n" + uptime.stdout, ephemeral=not public)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await ctx.respond("An error occurred while executing the command.", ephemeral=True)

    @discord.command(name="meow", description="meow", integration_types=[discord.IntegrationType.user_install])
    async def meow(self, ctx: discord.ApplicationContext):
        if ctx.user.id != int(OWNER):
            await ctx.respond("You are not authorized to use this command!", ephemeral=True)
            return

        await ctx.respond(f"meow\n-# Clicking the meow button will cause the bot to meow at you. The bot is very much normal, same as its Ai, <@{OWNER}>.", view=MeowComponent())

    @discord.command(name="silly", description="silly", integration_types=[discord.IntegrationType.user_install])
    async def silly(self, ctx: discord.ApplicationContext, text: str, title: str, label: str, placeholder: str = ""):
        if ctx.user.id != int(OWNER):
            await ctx.respond("You are not authorized to use this command!", ephemeral=True)
            return

        await ctx.respond(text, view=SillyComponent(title, label, placeholder))
