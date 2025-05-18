import os.path
import random
import re
import shutil
import string
import subprocess
import sys
import time

import aiohttp
import discord
import sentry_sdk
import yt_dlp.version
from dateutil.parser import isoparse
from discord.ext import tasks, commands

from constants import OWNER, FEDI_INSTANCE, GUILD, CHANNEL_MODERATION, FEDI_TOKEN, CHANNEL_MEMES, VERSION, FEDI_USER_ID
from util.keysmash_generator import keysmash_ai
from util.quarantine import add_member_to_quarantine, is_member_in_quarantine, delete_member_from_quarantine

dm_cache = []


def generate_meow():
    meow = random.choice(["meow", "nya", "mraow", "mwrmmwra"])

    if meow == "nya":
        return "ny" + random.randint(1, 8) * "a"
    elif meow == "mwrmmwra":
        meow = "mr"
        for i in range(random.randint(4, 12)):
            meow += random.choice(["a", "w", "r"])

        return meow

    return meow


def generate_fluster():
    fluster_type = random.choice([">///<", "keysmash"])
    if fluster_type == ">///<":
        return ">" + "/" * random.randint(3, 10) + "<"
    elif fluster_type == "keysmash":
        return "".join(random.choices(string.ascii_lowercase, k=random.randint(3, 25))) + " >" + "/" * random.randint(3,
                                                                                                                      10) + "<"
    else:
        raise ValueError("Invalid fluster type")


class PickerComponent(discord.ui.View):
    def __init__(self, type: str):
        super().__init__(timeout=None)

        if type == "meow":
            meow_btn = discord.ui.Button(style=discord.ButtonStyle.primary, label="Meow", custom_id="picker_meow")
            meow_btn.callback = self.meow
            self.add_item(meow_btn)
        elif type == "fedi meow":
            meow_btn = discord.ui.Button(style=discord.ButtonStyle.primary, label="Meow", custom_id="picker_meow_fedi")
            meow_btn.callback = self.meow_fedi
            self.add_item(meow_btn)
        elif type == ":3":
            colon_three_button = discord.ui.Button(style=discord.ButtonStyle.primary, label=":3",
                                                   custom_id="picker_colon_three")
            colon_three_button.callback = self.colon_three
            self.add_item(colon_three_button)
        elif type == "fedi :3":
            colon_three_button = discord.ui.Button(style=discord.ButtonStyle.primary, label=":3",
                                                   custom_id="picker_colon_three_fedi")
            colon_three_button.callback = self.colon_three_fedi
            self.add_item(colon_three_button)
        elif type == "compliments":
            # cute
            cute_button = discord.ui.Button(style=discord.ButtonStyle.primary, label="such a cute girl~ :3",
                                            custom_id="picker_cute")
            cute_button.callback = self.cute
            self.add_item(cute_button)

            # pretty
            pretty_button = discord.ui.Button(style=discord.ButtonStyle.primary, label="such a pretty girl~ :3",
                                              custom_id="picker_pretty")
            pretty_button.callback = self.pretty
            self.add_item(pretty_button)

            # gorgeous

            gorgeous_button = discord.ui.Button(style=discord.ButtonStyle.primary, label="such a gorgeous girl :3",
                                                custom_id="picker_gorgeous")
            gorgeous_button.callback = self.gorgeous
            self.add_item(gorgeous_button)

            # cool

            cool_button = discord.ui.Button(style=discord.ButtonStyle.primary, label="such a cool girl~ :3",
                                            custom_id="picker_cool")
            cool_button.callback = self.cool
            self.add_item(cool_button)

            # good girl

            good_girl_button = discord.ui.Button(style=discord.ButtonStyle.primary, label="such a goooood girl~ :3",
                                                 custom_id="picker_good_girl")
            good_girl_button.callback = self.good_girl
            self.add_item(good_girl_button)
        elif type == "meowat":
            meow_at_button = discord.ui.Button(style=discord.ButtonStyle.primary, label="meow at Lunya :3",
                                               custom_id="picker_meow_at")
            meow_at_button.callback = self.meowat
            self.add_item(meow_at_button)
        elif type == "purrr":
            purrr_button = discord.ui.Button(style=discord.ButtonStyle.primary, label="purrr :3",
                                             custom_id="picker_purrr")
            purrr_button.callback = self.purrr
            self.add_item(purrr_button)
        elif type == "girlkiss":
            girlkiss_button = discord.ui.Button(style=discord.ButtonStyle.primary,
                                                label="girlkiss a girl Lunya :3 (real) UwU",
                                                custom_id="picker_girlkiss")
            girlkiss_button.callback = self.girlkiss
            self.add_item(girlkiss_button)
        elif type == "boop":
            boop_button = discord.ui.Button(style=discord.ButtonStyle.primary, label="boop :3", custom_id="picker_boop")
            boop_button.callback = self.boop
            self.add_item(boop_button)
        elif type == "paws":
            paws_at_you_button = discord.ui.Button(style=discord.ButtonStyle.primary, label="*paws at you*",
                                                   custom_id="picker_paws")
            paws_at_you_button.callback = self.paws_at_you
            self.add_item(paws_at_you_button)
        else:
            raise ValueError("Invalid type")

    async def meow(self, interaction: discord.Interaction):
        try:
            meow = generate_meow()
            await interaction.respond(f"✅ Message sent\n{meow} :3", ephemeral=True)
            dm_cache.append(f"{meow} by {interaction.user.mention} :3", ephemeral=True)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await interaction.respond("An error occurred", ephemeral=True)

    async def meow_fedi(self, interaction: discord.Interaction):
        try:
            meow = generate_meow()
            await interaction.respond(f"✅ Message sent\n{meow} :3", ephemeral=True)

            async with aiohttp.ClientSession() as session:
                async with session.post(f"https://{FEDI_INSTANCE}/api/notes/create", json={
                    'text': f'@mld {meow} by {interaction.user.display_name} :3',
                    'visibility': 'specified',
                    'visibleUserIds': [
                        FEDI_USER_ID
                    ]
                }, headers={
                    'Authorization': f'Bearer {FEDI_TOKEN}'
                }) as req:

                    if not req.ok:
                        message = await req.text()
                        raise ValueError(f"Fedi Meow failed with code {req.status}: {req.reason} {message}")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await interaction.respond("An error occurred", ephemeral=True)

    async def colon_three(self, interaction: discord.Interaction):
        try:
            colon_three = ':' + '3' * random.randint(4, 12)
            await interaction.respond(f"✅ Message sent\n:{colon_three} :3", ephemeral=True)
            dm_cache.append(f"{colon_three} by {interaction.user.mention} :3")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await interaction.respond("An error occurred", ephemeral=True)

    async def colon_three_fedi(self, interaction: discord.Interaction):
        try:
            colon_three = ':' + '3' * random.randint(4, 12)
            await interaction.respond(f"✅ Message sent\n{colon_three} :3", ephemeral=True)

            async with aiohttp.ClientSession() as session:
                async with session.post(f"https://{FEDI_INSTANCE}/api/notes/create", json={
                    'text': f'@mld {colon_three} by {interaction.user.display_name} :3',
                    'visibility': 'specified',
                    'visibleUserIds': [
                        FEDI_USER_ID
                    ]
                }, headers={
                    'Authorization': f'Bearer {FEDI_TOKEN}'
                }) as req:
                    if not req.ok:
                        message = await req.text()
                        raise ValueError(f"Fedi Meow failed with code {req.status}: {req.reason} {message}")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await interaction.respond("An error occurred", ephemeral=True)

    async def cute(self, interaction: discord.Interaction):
        try:
            await interaction.respond(f"✅ {generate_fluster()}", ephemeral=True)
            dm_cache.append(f"{interaction.user.mention} said that you're such a cute girl~ :3")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await interaction.respond("An error occurred", ephemeral=True)

    async def pretty(self, interaction: discord.Interaction):
        try:
            await interaction.respond(f"✅ {generate_fluster()}", ephemeral=True)
            dm_cache.append(f"{interaction.user.mention} said that you're such a pretty girl~ :3")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await interaction.respond("An error occurred", ephemeral=True)

    async def gorgeous(self, interaction: discord.Interaction):
        try:
            await interaction.respond(f"✅ {generate_fluster()}", ephemeral=True)
            dm_cache.append(f"{interaction.user.mention} said that you're such a gorgeous girl~ :3")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await interaction.respond("An error occurred", ephemeral=True)

    async def cool(self, interaction: discord.Interaction):
        try:
            await interaction.respond(f"✅ {generate_fluster()}", ephemeral=True)
            dm_cache.append(f"{interaction.user.mention} said that you're such a coool girl~ :3")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await interaction.respond("An error occurred", ephemeral=True)

    async def good_girl(self, interaction: discord.Interaction):
        try:
            await interaction.respond(f"✅ {generate_fluster()} {generate_fluster()}", ephemeral=True)
            dm_cache.append(f"{interaction.user.mention} said that you're such a goooood girl~ :3")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await interaction.respond("An error occurred", ephemeral=True)

    async def meowat(self, interaction: discord.Interaction):
        try:
            await interaction.respond(f"✅ meow -> <@{OWNER}>", ephemeral=True)
            dm_cache.append(f"{interaction.user.mention} meowd at you :3")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await interaction.respond("An error occurred", ephemeral=True)

    async def purrr(self, interaction: discord.Interaction):
        try:
            await interaction.respond("✅ *purrrrrrr*", ephemeral=True)
            dm_cache.append(f"{interaction.user.mention} has *purrrrr* :3")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await interaction.respond("An error occurred", ephemeral=True)

    async def girlkiss(self, interaction: discord.Interaction):
        try:
            await interaction.respond("✅ Girls were kissed :3", ephemeral=True)
            dm_cache.append(f"{interaction.user.mention} has give you girlkiss :3333333333")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await interaction.respond("An error occurred", ephemeral=True)

    async def boop(self, interaction: discord.Interaction):
        try:
            await interaction.respond("✅ >///<", ephemeral=True)
            dm_cache.append(f"{interaction.user.mention} has booped you :3")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await interaction.respond("An error occurred", ephemeral=True)

    async def paws_at_you(self, interaction: discord.Interaction):
        try:
            await interaction.respond("✅ *paws at mldchan*", ephemeral=True)
            dm_cache.append(f"{interaction.user.mention} *paws at you* :3")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await interaction.respond("An error occurred", ephemeral=True)


def generate_user_embed(resp_body):
    host = FEDI_INSTANCE if resp_body["host"] is None else resp_body["host"]
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

    if resp_body["host"] is not None:
        emb.set_footer(text="The information may not be accurate as it comes from a remote instance.")

    return emb


async def lookup_user(user_name: str, user_inst: str | None, disable_pinned: bool = False, pinned_count: int = 3) -> \
        list[discord.Embed] | None:
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

            emb = generate_user_embed(resp_body)

            if disable_pinned:
                return [emb]

            pinned_notes = []
            i = 0
            for post in resp_body["pinnedNotes"]:
                i = i + 1
                if i > pinned_count:
                    break

                pinned_notes.append(generate_note_embed(post, pinned=True))

            return [emb, *pinned_notes]


def generate_note_embed(note, pinned=False):
    image_url = note["files"][0]["url"] if len(note["files"]) > 0 and note[
        'cw'] is None else None

    reaction_string = ""

    if note["repliesCount"] > 0:
        reaction_string = f'{note["repliesCount"]} replies | '

    if note['renoteCount'] > 0:
        reaction_string = f'{note["renoteCount"]} renotes | '

    for k, v in note["reactions"].items():
        if len(k.split("@")) > 1:
            k = f'{k.split("@")[0]}:'

        reaction_string += f'{v}x {k} | '

    reaction_string = reaction_string[:-3]

    host = FEDI_INSTANCE if note['user']['host'] is None else note['user']['host']

    pinned_post = "Pinned note by " if pinned else ""

    desc = note["text"] if note["cw"] is None else f'CW: {note["cw"]}\n\n'

    if note['cw'] is not None:
        if len(note['files']) > 0 and len(note['text']) > 0:
            desc += "(Open the link in order to view the text and media)"
        elif len(note['files']) > 0 and len(note['text']) == 0:
            desc += "(Open the link in order to view the media)"
        else:
            desc += "(Open the link in order to view the text)"

    if 'poll' in note and note['poll'] is not None and note['cw'] is None:
        desc += get_poll_str(note['poll'])

    emb = discord.Embed(
        title=f"{'Pinned ' if pinned else ''}Note by {note['user']['name']} (@{note['user']['username']}@{host})",
        url=f"https://{FEDI_INSTANCE}/notes/{note['id']}",
        description=desc,
        image=image_url,
        author=discord.EmbedAuthor(
            name=f"{pinned_post}{note['user']['name']} (@{note['user']['username']}@{host})",
            icon_url=note["user"]["avatarUrl"],
            url=f'https://{FEDI_INSTANCE}/@{note["user"]["username"]}@{host}'
        ),
        color=discord.Color.from_rgb(255, 119, 255),
        footer=discord.EmbedFooter(
            text=reaction_string
        ) if len(reaction_string) > 0 else None
    )

    return emb


async def lookup_note_id(note_id: str, pinned: bool = False) -> list[discord.Embed] | None:
    async with aiohttp.ClientSession() as session:
        async with session.post(f"https://{FEDI_INSTANCE}/api/notes/show", json={
            "noteId": note_id
        }) as resp:
            if resp.status != 200:
                return None

            resp_body = await resp.json()

            emb = generate_note_embed(resp_body, pinned)

            return [emb]


async def get_posts_under_hashtags(lookup_str) -> list[discord.Embed] | None:
    # Lookup_str: #art for example
    embeds = []

    async with aiohttp.ClientSession() as session:
        async with session.post(f"https://{FEDI_INSTANCE}/api/hashtags/show", json={
            'tag': lookup_str[1:]
        }) as resp:
            if resp.status != 200:
                return None

            body = await resp.json()

            embeds.append(
                discord.Embed(
                    title=f"Hashtag: {lookup_str}",
                    fields=[
                        discord.EmbedField(name="Posts", value=str(body['attachedUsersCount'])),
                        discord.EmbedField(name="User Mentions", value=str(body['mentionedUsersCount']))
                    ],
                    color=discord.Color.from_rgb(255, 119, 255)
                )
            )

        async with session.post(f"https://{FEDI_INSTANCE}/api/notes/search-by-tag", json={
            'limit': 10,
            'tag': lookup_str[1:]
        }) as resp:
            if resp.status != 200:
                return None

            body = await resp.json()

            for i in body[:3]:
                embeds.append(generate_note_embed(i))

    return embeds


async def lookup_by_str(lookup_str: str, disable_pinned: bool = False, pinned_count: int = 3) -> list[
                                                                                                     discord.Embed] | None:
    user_mention = lookup_str.split("@")
    if len(user_mention) == 2:
        # Local user lookup
        return await lookup_user(user_mention[1], None, disable_pinned=disable_pinned, pinned_count=pinned_count)
    elif len(user_mention) == 3:
        # Remote user lookup
        return await lookup_user(user_mention[1], user_mention[2], disable_pinned=disable_pinned,
                                 pinned_count=pinned_count)

    # Check hashtag
    if re.match(r"#[a-zA-Z0-9]+", lookup_str):
        return await get_posts_under_hashtags(lookup_str)

    # Lookup note by MisskeyID
    return await lookup_note_id(lookup_str)


def get_poll_str(poll: dict | None) -> str:
    if poll is None:
        return ""

    message = "\n\n**[Poll]**\n"
    counts = sum([i['votes'] for i in poll['choices']])

    for i in poll['choices']:
        if counts == 0:
            message += f"**{i['text']}** - {i['votes']} votes\n"
        else:
            message += f"**{i['text']}** - {i['votes']} votes ({int(i['votes'] / counts * 100)}%)\n"

    message += "\n"

    if poll['multiple']:
        message += "**Multiple Choices** - "

    expires_at = isoparse(poll['expiresAt'])
    message += f"**Expires at {expires_at.strftime('%Y/%m/%d %H:%M:%S %Z')}**\n"

    return message.rstrip()


async def search(query: str, content_type: str, media_type: str, count: int) -> tuple[list[discord.Embed], int] | None:
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        if content_type == 'notes':
            return await search_notes(query, media_type, session, start_time, count)
        elif content_type == 'users':
            return await search_users(query, session, start_time, count)

        raise ValueError(f"content_type is out of range: {content_type} is not a valid value")


async def search_users(query, session, start_time, count):
    async with session.post(f"https://{FEDI_INSTANCE}/api/users/search", json={
        'limit': 10,
        'query': query
    }) as resp:
        if resp.status != 200:
            return None

        resp_body = await resp.json()

        embeds = []

        for i in resp_body:
            emb = generate_user_embed(i)

            if emb is None:
                continue

            embeds.append(emb)

            if len(embeds) >= count:
                break

        end_time = time.time()
        diff = round((end_time - start_time) * 1000)
        return (embeds, diff) if len(embeds) > 0 else None


async def search_notes(query, media_type, session, start_time, count):
    body = {
        "query": query,
        "limit": 25
    }

    if media_type != "all" and media_type in ["image", "video"]:
        body["filetype"] = media_type

    async with session.post(f"https://{FEDI_INSTANCE}/api/notes/search", json=body) as resp:
        if resp.status != 200:
            return None

        resp_body = await resp.json()

        embeds = []

        for i in resp_body:
            if i["cw"] is not None:
                continue

            emb = generate_note_embed(i)

            if emb is None:
                continue

            embeds.append(emb)

            if len(embeds) >= count:
                break

        end_time = time.time()
        diff = round((end_time - start_time) * 1000)
        return (embeds[:count], diff) if len(embeds) > 0 else None


async def uwuify(text: str) -> str | None:
    # Send request
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=1)) as session:
        async with session.post("https://uwu.pm/api/v1/uwu", json={
            "text": text,
            "provider": "uwwwupp"
        }) as res:

            if res.status != 200:
                return None

            res = await res.json()

            if "uwu" not in res or res["uwu"] is None:
                return None

            return res["uwu"]


class UserCommands(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(PickerComponent("meow"))
        self.bot.add_view(PickerComponent("fedi meow"))
        self.bot.add_view(PickerComponent(":3"))
        self.bot.add_view(PickerComponent("fedi :3"))
        self.bot.add_view(PickerComponent("compliments"))
        self.bot.add_view(PickerComponent("meowat"))
        self.bot.add_view(PickerComponent("purrr"))
        self.bot.add_view(PickerComponent("girlkiss"))
        self.bot.add_view(PickerComponent("boop"))
        self.bot.add_view(PickerComponent("paws"))
        self.handle_queue.start()

    user_commands = discord.SlashCommandGroup(name='user', description='User commands',
                                              integration_types=[discord.IntegrationType.user_install])

    @user_commands.command(name='ping', description='Tests connection to Discord',
                           integration_types=[discord.IntegrationType.user_install])
    async def ping(self, ctx: discord.ApplicationContext):
        await ctx.respond(f'Pong! {self.bot.latency * 1500} ms', ephemeral=(ctx.user.id != int(OWNER)))

    @user_commands.command(name='message', description='Send message as bot',
                           integration_types=[discord.IntegrationType.user_install])
    async def message(self, ctx: discord.ApplicationContext, msg: str):
        if ctx.user.id != int(OWNER):
            await ctx.respond("You are not authorized to use this command!", ephemeral=True)
            return

        await ctx.respond(msg)

    @user_commands.command(name="information", description="Print information about the server",
                           integration_types=[discord.IntegrationType.user_install])
    async def information(self, ctx: discord.ApplicationContext, public: bool = False):
        try:
            if ctx.user.id != int(OWNER):
                await ctx.respond("You are not authorized to use this command!", ephemeral=True)
                return

            uname = subprocess.run(["uname", "-snrvmpio"], capture_output=True, text=True)
            uptime = subprocess.run(["uptime"], capture_output=True, text=True)
            version = (f"Python {sys.version} on {sys.platform}\n"
                      f"py-cord {discord.__version__}\n"
                      f"sentry_sdk {sentry_sdk.VERSION}\n"
                      f"yt_dlp {yt_dlp.version.__version__} {yt_dlp.version.CHANNEL}\n")

            await ctx.respond(f"# 愛OS (AiOS) version {VERSION}\n"
                              f"```\n"
                              f"{uname.stdout.strip()}\n"
                              f"{uptime.stdout.strip()}\n"
                              f"{version}"
                              f"```",
                              ephemeral=not public)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await ctx.respond("An error occurred while executing the command.", ephemeral=True)

    @user_commands.command(name="picker")
    async def picker(self, ctx: discord.ApplicationContext,
                     message: str,
                     type: discord.Option(str,
                                          choices=["meow", "fedi meow", ":3", "fedi :3", "compliments", "meowat", "purrr", "girlkiss", "boop",
                                                   "paws"])):
        try:
            if ctx.user.id != int(OWNER):
                await ctx.respond("You are not authorized to use this command!", ephemeral=True)
                return

            await ctx.respond(message, view=PickerComponent(type))
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await ctx.respond("An error occurred while executing the command.", ephemeral=True)

    fedi_group = discord.SlashCommandGroup(name="fedi", description="Fedi commands",
                                           integration_types=[discord.IntegrationType.user_install])

    @fedi_group.command(name="lookup", description="Lookup fedi user/post",
                        integration_types=[discord.IntegrationType.user_install])
    async def lookup_post(self, ctx: discord.ApplicationContext, lookup_str: str, disable_pinned: bool = False,
                          pinned_count: int = 3):
        try:
            # Verify right user
            if ctx.user.id != int(OWNER):
                await ctx.respond("You are not authorized to use this command!", ephemeral=True)
                return

            # Let's attempt generate embed based on lookup function
            emb = await lookup_by_str(lookup_str, disable_pinned=disable_pinned, pinned_count=pinned_count)

            if emb is None:
                await ctx.respond("Failed to lookup!", ephemeral=True)
                return

            await ctx.respond(embeds=emb)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await ctx.respond("Error when looking up!", ephemeral=True)

    @fedi_group.command(name="search", description="Search on fedi",
                        integration_types=[discord.IntegrationType.user_install])
    @discord.option(name="media_type", choices=["image", "video"])
    @discord.option(name="content_type", choices=["notes", "users"])
    @discord.option(name="count", min=1, max=10)
    async def search(self, ctx: discord.ApplicationContext, q: str, content_type: str = 'notes',
                     media_type: str = 'all', count: int = 3):
        try:
            # Verify right user
            if ctx.user.id != int(OWNER):
                await ctx.respond("You are not authorized to use this command!", ephemeral=True)
                return

            await ctx.defer()

            # Let's attempt to generate embed based on search function
            emb = await search(q, content_type, media_type, count)

            if emb is None:
                await ctx.followup.send("Error! No result")
                return

            await ctx.followup.send(embeds=emb[0], content=f"Searched 3,089,841+ notes within {emb[1]} ms")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await ctx.followup.send(f"Error! Server error: {e=}")

    @fedi_group.command(name="note", description="Create a note on fedi",
                        integration_types=[discord.IntegrationType.user_install])
    @discord.option(name="visibility", choices=["public", "home", "followers"])
    async def note(self, ctx: discord.ApplicationContext, text: str, cw: str = "", visibility: str = "public",
                   public_response: bool = False):
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

                    await ctx.respond(f"Note created! https://{FEDI_INSTANCE}/notes/{data['createdNote']['id']}",
                                      ephemeral=not public_response)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await ctx.respond("Failed to create note!", ephemeral=True)

    @user_commands.command(name='ban_from_mldchan', description='Ban user from mldchan\'s Discord server',
                           integration_types=[discord.IntegrationType.user_install])
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

    @user_commands.command(name='add_to_quarantine', description='Add user to quarantine of mldchan',
                           integration_types=[discord.IntegrationType.user_install])
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

    @user_commands.command(name='remove_from_quarantine', description='Add user to quarantine of mldchan',
                           integration_types=[discord.IntegrationType.user_install])
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

    @user_commands.command(name="uwwwu", description="UwUify text",
                           integration_types=[discord.IntegrationType.user_install])
    async def uwuify_text(self, ctx: discord.ApplicationContext, text: str, private: bool = True):
        try:
            # Verify right user
            if ctx.user.id != int(OWNER):
                await ctx.respond("You are not authorized to use this command!", ephemeral=True)
                return

            # Send request
            uwuified = await uwuify(text)
            if uwuified is None:
                await ctx.respond("An error occured!", ephemeral=True)
                return

            await ctx.respond(uwuified, ephemeral=not private)
        except Exception as e:
            await ctx.respond(f"An error occured! {e=}", ephemeral=True)
            sentry_sdk.capture_exception(e)

    @discord.slash_command(name="uwuify", description="UwUify text")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def uwuify_text_public(self, ctx: discord.ApplicationContext, text: str, use_ai: discord.Option(bool,
                                                                                                          description="Do you want to use the latest cutting-edge AI to uwuify?",
                                                                                                          default=True)):
        try:
            # Cutting-edge AI check
            if use_ai:
                await ctx.respond(keysmash_ai(), ephemeral=True)
                return

            # Send request
            uwuified = await uwuify(text)
            if uwuified is None:
                await ctx.respond("An error occured!", ephemeral=True)
                return

            await ctx.respond(uwuified, ephemeral=True)
        except Exception as e:
            await ctx.respond(f"An error occured! {e=}", ephemeral=True)
            sentry_sdk.capture_exception(e)

    @discord.message_command(name='Borrow Meme',
                             description='Repost the message inside of the memes channel of mldchan\'s Discord server',
                             integration_types=[discord.IntegrationType.user_install])
    async def borrow_meme(self, ctx: discord.ApplicationContext, message: discord.Message):
        try:
            if ctx.user.id != int(OWNER):
                await ctx.respond("You are not authorized to use this command!", ephemeral=True)

            # Download all attachments
            if not os.path.exists("temp"):
                os.mkdir("temp")

            for i in message.attachments:
                with open("temp/" + i.filename, "wb") as f:
                    await i.save(f)

            # Send it
            memes = self.bot.get_guild(int(GUILD)).get_channel(int(CHANNEL_MEMES))
            await memes.send(content=message.content,
                             files=[discord.File(f"temp/{i.filename}", i.filename) for i in message.attachments])

            # Delete
            shutil.rmtree("temp")

            await ctx.respond("Meme reposted in mldchan server successfully!", ephemeral=True)
        except Exception as e:
            await ctx.respond("Error!", ephemeral=True)
            sentry_sdk.capture_exception(e)

    @discord.slash_command(name="version", description="Print bot version")
    async def version(self, ctx: discord.ApplicationContext):
        try:
            await ctx.respond(f"# 愛OS (AiOS) version {VERSION}\n\n"
                              f"Python {sys.version} on {sys.platform}\n"
                              f"py-cord {discord.__version__}\n"
                              f"sentry_sdk {sentry_sdk.VERSION}\n"
                              f"yt_dlp {yt_dlp.version.__version__} {yt_dlp.version.CHANNEL}\n\n"
                              f"Licensed under GNU AGPL v3.0. Software's source code is [here](<https://code.mldchan.dev/mld/Ai>)", ephemeral=True)
        except Exception as e:
            await ctx.respond("Error!", ephemeral=True)
            sentry_sdk.capture_exception(e)

    @tasks.loop(seconds=20)
    async def handle_queue(self):
        try:
            if len(dm_cache) == 0:
                return

            message = "\n".join(dm_cache)

            owner = self.bot.get_user(int(OWNER))
            await owner.send(message)

            dm_cache.clear()
        except Exception as e:
            sentry_sdk.capture_exception(e)
