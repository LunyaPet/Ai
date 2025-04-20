import random
import subprocess
import time

import aiohttp
import discord
import sentry_sdk
from discord import Interaction

from constants import OWNER, FEDI_INSTANCE, GUILD, CHANNEL_MODERATION


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
            uptime = subprocess.run(["uptime", "-p"], capture_output=True, text=True)

            await ctx.respond(uname.stdout.strip() + "\n" + uptime.stdout.strip(), ephemeral=not public)
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

    fedi_group = discord.SlashCommandGroup(name="fedi", description="Fedi commands", integration_types=[discord.IntegrationType.user_install])

    @fedi_group.command(name="lookup", description="Lookup fedi user/post")
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

    @fedi_group.command(name="search", description="Search on fedi")
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

    @discord.slash_command(name='ban_from_mldchan', description='Ban user from mldchan\'s Discord server')
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
                description=f"The member {user.mention} was banned here because mldchan issued a ban command from the {ctx.guild.name} Discord server.",
                fields=[
                    discord.EmbedField(name="Banned Member", value=user.mention, inline=True),
                    discord.EmbedField(name="Reason", value=reason, inline=True),
                    discord.EmbedField(name="From Server", value=ctx.guild.name, inline=True)
                ]
            ))

            await ctx.respond("Member was banned successfully!", ephemeral=True)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await ctx.respond("An error occured reporting this user.", ephemeral=True)
