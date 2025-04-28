import random
import subprocess
import time

import aiohttp
import discord
import sentry_sdk
from discord import Interaction
from discord.ext import tasks

from constants import OWNER, FEDI_INSTANCE, GUILD, CHANNEL_MODERATION, FEDI_TOKEN
from util.quarantine import add_member_to_quarantine, is_member_in_quarantine, delete_member_from_quarantine


class MeowComponent(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Meow", style=discord.ButtonStyle.primary, custom_id="uc_meow")
    async def meow(self, button: discord.ui.Button, interaction: discord.Interaction):
        meows = ["Mraow~", "meow :3", "mwmrwmrma~ :3 ", "mwrmwmrwma :3", "mwrmwma :3", "meow", "mmrwwa uwu :3"]
        await interaction.respond(random.choice(meows), ephemeral=True)

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

async def lookup_user(user_name: str, user_inst: str | None) -> list[discord.Embed] | None:
    async with aiohttp.ClientSession() as session:
        body = {
            "username": user_name,
        }

        if user_inst is not None:
            body["host"] = user_inst

        async with session.post(f"https://{FEDI_INSTANCE}/api/users/show", json=body) as resp:
            if resp.status != 200:
                return None

            resp_body = await resp.json()

            host = FEDI_INSTANCE if user_inst is None else user_inst
            desc = resp_body["description"][:1500]
            if desc != resp_body["description"]:
                desc = desc + '...'

            emb = discord.Embed(
                title=f"{resp_body['name']} (@{resp_body['username']}@{host})",
                description=desc,
                thumbnail=resp_body["avatarUrl"],
                fields=[
                    discord.EmbedField(name="Notes", value=resp_body["notesCount"], inline=True),
                    discord.EmbedField(name="Followers", value=resp_body["followersCount"], inline=True),
                    discord.EmbedField(name="Following", value=resp_body["followingCount"], inline=True)
                ],
                url=f'https://{FEDI_INSTANCE}/@{resp_body["username"]}@{host}',
                color=discord.Color.from_rgb(255, 119, 255)
            )

            if user_inst is not None:
                emb.set_footer(text="The information may not be accurate as it comes from a remote instance.")

            pinned_notes = []
            i = 0
            for post in resp_body["pinnedNotes"]:
                i = i + 1
                if i > 2:
                    break

                pinned_notes.extend(await lookup_note_id(post["id"], pinned=True))

            return [emb, *pinned_notes]


async def lookup_note_id(note_id: str, pinned: bool = False) -> list[discord.Embed] | None:
    async with aiohttp.ClientSession() as session:
        async with session.post(f"https://{FEDI_INSTANCE}/api/notes/show", json={
            "noteId": note_id
        }) as resp:
            if resp.status != 200:
                return None

            resp_body = await resp.json()

            image_url = resp_body["files"][0]["url"] if len(resp_body["files"]) > 0 else None

            reaction_string = ""

            if resp_body["repliesCount"] > 0:
                reaction_string = f'{resp_body["repliesCount"]} replies | '

            if resp_body['renoteCount'] > 0:
                reaction_string = f'{resp_body["renoteCount"]} renotes | '

            for k, v in resp_body["reactions"].items():
                if len(k.split("@")) > 1:
                    k = f'{k.split("@")[0]}:'

                reaction_string += f'{v}x {k} | '

            reaction_string = reaction_string[:-3]

            host = FEDI_INSTANCE if resp_body['user']['host'] is None else resp_body['user']['host']

            pinned_post = "Pinned note by " if pinned else ""

            emb = discord.Embed(
                title=f"{'Pinned ' if pinned else ''}Note by {resp_body['user']['name']} (@{resp_body['user']['username']}@{host})",
                url=f"https://{FEDI_INSTANCE}/notes/{resp_body['id']}",
                description=resp_body["text"] if resp_body["cw"] is None else f'CW: {resp_body["cw"]}',
                image=image_url,
                author=discord.EmbedAuthor(
                    name=f"{pinned_post}{resp_body['user']['name']} (@{resp_body['user']['username']}@{host})",
                    icon_url=resp_body["user"]["avatarUrl"],
                    url=f'https://{FEDI_INSTANCE}/@{resp_body["user"]["username"]}@{host}'
                ),
                color=discord.Color.from_rgb(255, 119, 255),
                footer=discord.EmbedFooter(
                    text=reaction_string
                ) if len(reaction_string) > 0 else None
            )

            return [emb]


async def lookup_by_str(lookup_str: str) -> list[discord.Embed] | None:

    user_mention = lookup_str.split("@")
    if len(user_mention) == 2:
        # Local user lookup
        return await lookup_user(user_mention[1], None)
    elif len(user_mention) == 3:
        # Remote user lookup
        return await lookup_user(user_mention[1], user_mention[2])

    # Lookup note by MisskeyID

    return await lookup_note_id(lookup_str)


async def search(query: str) -> tuple[list[discord.Embed], int] | None:
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.post(f"https://{FEDI_INSTANCE}/api/notes/search", json={
            "query": query,
            "limit": 10
        }) as resp:
            if resp.status != 200:
                return None

            resp_body = await resp.json()

            embeds = []

            for i in resp_body:
                emb = await lookup_note_id(i["id"])

                if emb is None:
                    continue

                embeds.extend(emb)

                if len(embeds) >= 3:
                    break

            end_time = time.time()
            diff = round((end_time - start_time) * 1000)
            return (embeds, diff) if len(embeds) > 0 else None


compliments_cache = {}

def count_cache(compl_type: str, user_id: str):
    if compl_type not in compliments_cache:
        compliments_cache[compl_type] = []

    compliments_cache[compl_type].append(user_id)


def get_cache_str():
    compl_str = "You were called "
    for (k, v) in compliments_cache.items():
        compl_str += f"{len(v)}x {k} by "
        for i in v:
            compl_str += f"<@{i}>, "

        compl_str = compl_str[:-2] + ", "

    return compl_str[:-2]

def clear_cache():
    compliments_cache.clear()

class UserCommands(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(MeowComponent())
        self.bot.add_view(ComplimentsView(self.bot))
        self.handle_queue.start()

    user_commands = discord.SlashCommandGroup(name='user', description='User commands', integration_types=[discord.IntegrationType.user_install])

    @user_commands.command(name='ping', description='Tests connection to Discord', integration_types=[discord.IntegrationType.user_install])
    async def ping(self, ctx: discord.ApplicationContext):
        await ctx.respond(f'Pong! {self.bot.latency * 1500} ms', ephemeral=(ctx.user.id != int(OWNER)))

    @user_commands.command(name='message', description='Send message as bot', integration_types=[discord.IntegrationType.user_install])
    async def message(self, ctx: discord.ApplicationContext, msg: str):
        if ctx.user.id != int(OWNER):
            await ctx.respond("You are not authorized to use this command!", ephemeral=True)
            return

        await ctx.respond(msg)

    @user_commands.command(name="information", description="Print information about the server", integration_types=[discord.IntegrationType.user_install])
    async def information(self, ctx: discord.ApplicationContext, public: bool = False):
        try:
            if ctx.user.id != int(OWNER):
                await ctx.respond("You are not authorized to use this command!", ephemeral=True)
                return

            uname = subprocess.run(["uname", "-a"], capture_output=True, text=True)
            uptime = subprocess.run(["uptime", "-p"], capture_output=True, text=True)

            await ctx.respond(uname.stdout.strip() + "\n" + uptime.stdout.strip(), ephemeral=not public)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await ctx.respond("An error occurred while executing the command.", ephemeral=True)

    @user_commands.command(name="meow", description="meow", integration_types=[discord.IntegrationType.user_install])
    async def meow(self, ctx: discord.ApplicationContext):
        if ctx.user.id != int(OWNER):
            await ctx.respond("You are not authorized to use this command!", ephemeral=True)
            return

        await ctx.respond(f"meow\n-# Clicking the meow button will cause the bot to meow at you. The bot is very much normal, same as its Ai, <@{OWNER}>.", view=MeowComponent())

    @user_commands.command(name="silly", description="silly", integration_types=[discord.IntegrationType.user_install])
    async def silly(self, ctx: discord.ApplicationContext, text: str, title: str, label: str, placeholder: str = ""):
        if ctx.user.id != int(OWNER):
            await ctx.respond("You are not authorized to use this command!", ephemeral=True)
            return

        await ctx.respond(text, view=SillyComponent(title, label, placeholder))

    fedi_group = discord.SlashCommandGroup(name="fedi", description="Fedi commands", integration_types=[discord.IntegrationType.user_install])

    @fedi_group.command(name="lookup", description="Lookup fedi user/post", integration_types=[discord.IntegrationType.user_install])
    async def lookup_post(self, ctx: discord.ApplicationContext, lookup_str: str):
        try:
            # Verify right user
            if ctx.user.id != int(OWNER):
                await ctx.respond("You are not authorized to use this command!", ephemeral=True)
                return

            # Let's attempt generate embed based on lookup function
            emb = await lookup_by_str(lookup_str)

            if emb is None:
                await ctx.respond("Failed to lookup!", ephemeral=True)
                return

            await ctx.respond(embeds=emb)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await ctx.respond("Error when looking up!", ephemeral=True)

    @fedi_group.command(name="search", description="Search on fedi", integration_types=[discord.IntegrationType.user_install])
    async def search(self, ctx: discord.ApplicationContext, q: str):
        try:
            # Verify right user
            if ctx.user.id != int(OWNER):
                await ctx.respond("You are not authorized to use this command!", ephemeral=True)
                return

            await ctx.defer()

            # Let's attempt to generate embed based on search function
            emb = await search(q)

            if emb is None:
                await ctx.followup.send("Error! No result")
                return

            await ctx.followup.send(embeds=emb[0], content=f"Searched 3,089,841+ notes within {emb[1]} ms")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await ctx.followup.send(f"Error! Server error: {e=}")

    @fedi_group.command(name="note", description="Create a note on fedi", integration_types=[discord.IntegrationType.user_install])
    @discord.option(name="visibility", choices=["public", "home", "followers"])
    async def note(self, ctx: discord.ApplicationContext, text: str, cw: str = "", visibility: str = "public", public_response: bool = False):
        try:
            # Try create a note
            data = {'text': text, 'visibility': visibility}
            if len(cw.strip()) > 0:
                data['cw'] = cw.strip()

            async with aiohttp.ClientSession() as session:
                async with session.post(f"https://{FEDI_INSTANCE}/api/notes/create", json=data, headers={
                    'Authorization': f'Bearer {FEDI_TOKEN}'
                }) as resp:
                    if resp.status != 200:
                        await ctx.respond("Non-OK response from server!", ephemeral=True)
                        text = await resp.text()

                        sentry_sdk.capture_message(f"Non-OK response {resp.status} from server: {text}")
                        return

                    data = await resp.json()

                    await ctx.respond(f"Note created! https://{FEDI_INSTANCE}/notes/{data['createdNote']['id']}", ephemeral=not public_response)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await ctx.respond("Failed to create note!", ephemeral=True)

    @user_commands.command(name='ban_from_mldchan', description='Ban user from mldchan\'s Discord server', integration_types=[discord.IntegrationType.user_install])
    async def ban_from_mldchan(self, ctx: discord.ApplicationContext, user: discord.User, reason: str):
        try:
            # Verify right user
            if ctx.user.id != int(OWNER):
                await ctx.respond("You are not authorized to use this command!", ephemeral=True)
                return

            # Get guild

            guild = self.bot.get_guild(int(GUILD))

            # Ban user

            await guild.ban(user, reason=reason, delete_message_seconds=7 * 24 * 3600)

            # Log message

            logs_channel = guild.get_channel(int(CHANNEL_MODERATION))

            await logs_channel.send(embed=discord.Embed(
                title="Member Banned Externally",
                description=f"The member {user.mention} was banned here because mldchan issued a ban command from a different server.",
                fields=[
                    discord.EmbedField(name="Banned Member", value=user.mention, inline=True),
                    discord.EmbedField(name="Reason", value=reason, inline=True)
                ]
            ))

            await ctx.respond("Member was banned successfully!", ephemeral=True)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await ctx.respond("An error occured banning this user.", ephemeral=True)

    @user_commands.command(name='add_to_quarantine', description='Add user to quarantine of mldchan', integration_types=[discord.IntegrationType.user_install])
    async def add_to_quarantine(self, ctx: discord.ApplicationContext, user: discord.User):
        try:
            # Verify right user
            if ctx.user.id != int(OWNER):
                await ctx.respond("You are not authorized to use this command!", ephemeral=True)
                return

            if is_member_in_quarantine(user.id):
                await ctx.respond("This user is already quarantined!", ephemeral=True)
                return

            add_member_to_quarantine(user.id)
            await ctx.respond("Member was added to quarantine successfully!", ephemeral=True)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await ctx.respond("An error occured quarantining this user.", ephemeral=True)

    @user_commands.command(name='remove_from_quarantine', description='Add user to quarantine of mldchan', integration_types=[discord.IntegrationType.user_install])
    async def remove_from_quarantine(self, ctx: discord.ApplicationContext, user: discord.User):
        try:
            # Verify right user
            if ctx.user.id != int(OWNER):
                await ctx.respond("You are not authorized to use this command!", ephemeral=True)
                return

            if not is_member_in_quarantine(user.id):
                await ctx.respond("This user is not quarantined!", ephemeral=True)
                return

            delete_member_from_quarantine(user.id)
            await ctx.respond("Member was removed from quarantine successfully!", ephemeral=True)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await ctx.respond("An error occured quarantining this user.", ephemeral=True)

    @user_commands.command(name='compliments', description='>//////<', integration_types=[discord.IntegrationType.user_install])
    async def compliments(self, ctx: discord.ApplicationContext):
        try:
            # Verify right user
            if ctx.user.id != int(OWNER):
                await ctx.respond("You are not authorized to use this command!", ephemeral=True)
                return

            await ctx.respond("Send a girl some compliments! :3", view=ComplimentsView(self.bot))
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await ctx.respond("Error!", ephemeral=True)

    @tasks.loop(seconds=5)
    async def handle_queue(self):
        try:
            if len(compliments_cache) == 0:
                return

            message = get_cache_str()

            owner = self.bot.get_user(int(OWNER))
            await owner.send(message)

            clear_cache()
        except Exception as e:
            sentry_sdk.capture_exception(e)

class ComplimentsView(discord.ui.View):
    def __init__(self, bot: discord.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="cute!", style=discord.ButtonStyle.primary, custom_id="cute")
    async def cute(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            count_cache("cute", str(interaction.user.id))

            await interaction.respond("Sent!", ephemeral=True)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await interaction.respond("An error occured in mldchan's code :(", ephemeral=True)


    @discord.ui.button(label="pretty!", style=discord.ButtonStyle.primary, custom_id="pretty")
    async def pretty(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            count_cache("pretty", str(interaction.user.id))

            await interaction.respond("Sent!", ephemeral=True)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await interaction.respond("An error occured in mldchan's code :(", ephemeral=True)


    @discord.ui.button(label="gorgeous!", style=discord.ButtonStyle.primary, custom_id="gorgeous")
    async def gorgeous(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            count_cache("gorgeous", str(interaction.user.id))

            await interaction.respond("Sent!", ephemeral=True)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await interaction.respond("An error occured in mldchan's code :(", ephemeral=True)


    @discord.ui.button(label="cool!", style=discord.ButtonStyle.primary, custom_id="cool")
    async def cool(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            count_cache("cool", str(interaction.user.id))

            await interaction.respond("Sent!", ephemeral=True)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await interaction.respond("An error occured in mldchan's code :(", ephemeral=True)


    @discord.ui.button(label="good girl!", style=discord.ButtonStyle.primary, custom_id="good_girl")
    async def good_girl(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            count_cache("good girl", str(interaction.user.id))

            await interaction.respond("Sent!", ephemeral=True)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await interaction.respond("An error occured in mldchan's code :(", ephemeral=True)


    @discord.ui.button(label=":3", style=discord.ButtonStyle.primary, custom_id="colon_three")
    async def colon_three(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            count_cache(":3", str(interaction.user.id))

            await interaction.respond("Sent!", ephemeral=True)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await interaction.respond("An error occured in mldchan's code :(", ephemeral=True)
