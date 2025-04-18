import discord
from constants import OWNER

class UserCommands(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.command(name='ping', description='Tests connection to Discord', integration_types=[discord.IntegrationType.user_install])
    async def ping(self, ctx: discord.ApplicationContext):
        await ctx.respond(f'Pong! {self.bot.latency * 1500} ms', ephemeral=(ctx.user.id != int(OWNER)))
