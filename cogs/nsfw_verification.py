import asyncio
import time

import discord
import sentry_sdk
from discord.ext import commands

from constants import ROLE_NSFW, GUILD
from util.storage import get_data, set_data


class NsfwView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=1800)
        self.start_timer = time.time()

    @discord.ui.button(label="i agree, gib access uwu", style=discord.ButtonStyle.primary)
    async def agree(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            end_timer = time.time()
            diff = end_timer - self.start_timer

            if diff < 10:
                await interaction.respond("you didn't read the disclaimer! please read it before continuing", ephemeral=True)
                return

            # double check
            nsfw_bans = get_data("nsfw_bans")
            if 'list' in nsfw_bans and str(interaction.user.id) in nsfw_bans['list']:
                await interaction.respond("sorry, you're banned.", ephemeral=True)
                return

            role = interaction.guild.get_role(int(ROLE_NSFW))

            self.stop()
            self.disable_all_items()

            await asyncio.gather(
                interaction.user.add_roles(role),
                interaction.edit(view=self),
                interaction.respond(
                    "you have been added to the nsfw section. if you don't see it, please check Channels and Roles.",
                    ephemeral=True)
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await interaction.respond("an error occured :(", ephemeral=True)


    @discord.ui.button(label="nvm", style=discord.ButtonStyle.secondary)
    async def disagree(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            self.stop()
            self.disable_all_items()
            await interaction.edit(view=self)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await interaction.respond("an error occured :(", ephemeral=True)

class NsfwRolePicker(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="nsfw access", style=discord.ButtonStyle.danger, custom_id="role_nsfw_access")
    async def nsfw_access(self, button: discord.ui.Button, interaction: discord.Interaction):

        nsfw_bans = get_data("nsfw_bans")
        if 'list' in nsfw_bans and str(interaction.user.id) in nsfw_bans['list']:
            await interaction.respond("sorry, you're banned.", ephemeral=True)
            return

        await interaction.respond("""# nsfw access
        
in order to access the nsfw section on this server, **please read the following carefully**:
- the nsfw section is 18+. any users that are under 18 will be **permanently banned** from the nsfw chats.
- you aren't allowed to post violent and gorey content. this will result in a ban.
- if you're ever banned from the nsfw section, you cannot return, even after being 18 or saying sorry.

understand? if yes, please continue below.""", ephemeral=True, view=NsfwView())


class NsfwVerification(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(NsfwRolePicker())

    @discord.message_command(name="nsfw ban", description="ban user from nsfw")
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @discord.default_permissions(kick_members=True)
    async def nsfw_ban(self, ctx: discord.ApplicationContext, message: discord.Message):
        try:
            if not ctx.guild and ctx.guild.id != GUILD:
                await ctx.respond("not compatible with current server", ephemeral=True)
                return

            # remove role from user
            role = ctx.guild.get_role(int(ROLE_NSFW))
            if role in message.author.roles:
                await message.author.remove_roles(role)

            # add to ban list
            ban_list = get_data("nsfw_bans")
            if 'list' not in ban_list:
                ban_list['list'] = []

            if str(message.author.id) not in ban_list:
                ban_list['list'].append(str(message.author.id))

            set_data("nsfw_bans", ban_list)

            await ctx.respond(f"banned {message.author.name}", ephemeral=True)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await ctx.respond("an error occured :(", ephemeral=True)

    @discord.command(name="unban_nsfw", description="unban user from nsfw")
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @discord.default_permissions(kick_members=True)
    async def nsfw_unban(self, ctx: discord.ApplicationContext, user: discord.User):
        try:
            if not ctx.guild and ctx.guild.id != GUILD:
                await ctx.respond("not compatible with current server", ephemeral=True)
                return

            # remove from ban list
            ban_list = get_data("nsfw_bans")
            if 'list' not in ban_list:
                ban_list['list'] = []

            if str(user.id) in ban_list['list']:
                ban_list['list'].remove(str(user.id))

            set_data("nsfw_bans", ban_list)

            await ctx.respond(f"unbanned {user.name}", ephemeral=True)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await ctx.respond("an error occured :(", ephemeral=True)

