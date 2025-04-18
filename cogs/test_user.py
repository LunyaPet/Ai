import discord
from constants import OWNER

class UserCommands(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.slash_command(name='ping', description='Tests connection to Discord')
    async def ping(self, ctx: discord.ApplicationContext):
        await ctx.respond('Pong!', ephemeral=(ctx.user.id != int(OWNER)))
