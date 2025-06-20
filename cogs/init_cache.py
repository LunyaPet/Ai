import asyncio
import logging

import discord
import sentry_sdk

from constants import GUILD, CHANNEL_MODERATION
from util.storage import set_data, get_data
from discord.ext import tasks


def compare_embeds(cached: list[dict], embeds: list[discord.Embed]):
    cached: list[discord.Embed] = [discord.Embed.from_dict(i) for i in cached]

    differences: list[tuple[str, str, str]] = []

    for (i, v) in enumerate(zip(cached, embeds)):
        if v[0].title != v[1].title:
            differences.append((f"Embed {i + 1} Title", v[0].title, v[1].title))
        if v[0].description != v[1].description:
            differences.append((f"Embed {i + 1} Description", v[0].description, v[1].description))

        if v[0].author is not None and v[1].author is not None:
            if v[0].author.name != v[1].author.name:
                differences.append((f"Embed {i + 1} Author", v[0].author.name, v[1].author.name))

        if v[0].footer is not None and v[1].footer is not None:
            if v[0].footer.text != v[1].footer.text:
                differences.append((f"Embed {i + 1} Footer", v[0].footer.text, v[1].footer.text))

        for (j, w) in enumerate(zip(v[0].fields, v[1].fields)):
            if w[0].name != w[1].name:
                differences.append((f"Embed {i + 1} Field {j + 1} Name", w[0].name, w[1].name))
            if w[0].value != w[1].value:
                differences.append((f"Embed {i + 1} Field {j + 1} Value", w[0].value, w[1].value))

    return differences


def get_reaction_dict(react: discord.Reaction):
    if isinstance(react.emoji, discord.PartialEmoji) or isinstance(react.emoji, discord.Emoji):
        return {
            "emojiname": react.emoji.name,
            "emojiid": react.emoji.id,
            "emojiurl": react.emoji.url,
            "count": react.count
        }
    elif isinstance(react.emoji, str):
        return {
            "emoji": react.emoji,
            "count": react.count
        }

    raise ValueError(f"Unexpected type {str(type(react))} in get_emoji_dict")


class InitCache(discord.Cog):
    def __init__(self, bot: discord.Bot):
        super().__init__()
        self.bot = bot
        self.cached_messages: list[dict] = []
        self.cached_users: list[dict] = []
        self.cached_channels: list[dict] = []
        self.cached_emojis: list[dict] = []
        self.load()
        self.saving_task.start()

    @tasks.loop(minutes=30)
    async def saving_task(self):
        self.save()

    async def init_channel(self, channel: discord.TextChannel):
        try:
            async for message in channel.history(limit=None):
                if self.message_is_cached(message):
                    break

                self.cache_message(message)

            logging.info(f"Caching channel #%s finished.", channel.name)
        except Exception as e:
            sentry_sdk.capture_exception(e)

    @discord.Cog.listener()
    async def on_ready(self):
        try:
            guild = self.bot.get_guild(int(GUILD))

            if guild is None:
                return

            logging.info("Counting %d channels...", len(guild.text_channels))

            await asyncio.gather(
                *[self.init_channel(i) for i in guild.text_channels]
            )

            self.save()
            logging.info(f"Created cache for %d messages and %d users", len(self.cached_messages),
                         len(self.cached_users))
        except Exception as e:
            sentry_sdk.capture_exception(e)

    def message_is_cached(self, message: discord.Message) -> bool:
        return any([i['id'] == message.id for i in self.cached_messages])

    def cache_message(self, message: discord.Message):
        if not any([i['id'] == message.id for i in self.cached_messages]):
            self.cached_messages.append({
                "id": message.id,
                "channelID": message.channel.id,
                "authorID": message.author.id,
                "content": message.content,
                "reactions": [get_reaction_dict(i) for i in message.reactions],
                "embeds": [i.to_dict() for i in message.embeds],
                "sentat": message.created_at.isoformat(timespec="minutes")
            })

        # Remove user if missing information
        b = [i for i in self.cached_users if i["id"] == message.author.id]
        if len(b) > 0 and "bot" not in b[0]:
            self.cached_users = [i for i in self.cached_users if i["id"] != message.author.id]

        if not any(i['id'] == message.author.id for i in self.cached_users):
            self.cached_users.append({
                "id": message.author.id,
                "username": message.author.name,
                "displayname": message.author.display_name,
                "avatar": message.author.display_avatar.url,
                "bot": message.author.bot
            })

        if not any(i['id'] == message.channel.id for i in self.cached_channels):
            self.cached_channels.append({
                "id": message.channel.id,
                "name": message.channel.name,
                "topic": message.channel.topic,
                "announcement": message.channel.is_news(),
                "nsfw": message.channel.is_nsfw()
            })

    def update_cached_message(self, message: discord.Message):
        self.cached_messages = [i for i in self.cached_messages if i['id'] != message.id]
        self.cached_users = [i for i in self.cached_users if i['id'] != message.author.id]
        self.cache_message(message)

    def get_cached_message(self, message_id: int):
        a = [i for i in self.cached_messages if i['id'] == message_id]
        return None if len(a) == 0 else a[0]

    def get_cached_user(self, user_id: int):
        a = [i for i in self.cached_users if i['id'] == user_id]
        return None if len(a) == 0 else a[0]

    def save(self):
        with sentry_sdk.start_transaction(op="task", name="Save cache"):
            logging.info("Writing bot_cache")
            set_data("bot_cache", {
                "messages": self.cached_messages,
                "users": self.cached_users,
                "channels": self.cached_channels
            })
            logging.info("Written bot_cache")

    def load(self):
        with sentry_sdk.start_transaction(op="task", name="Load cache"):
            logging.info("Loading bot_cache")
            data = get_data("bot_cache")

            if "messages" in data:
                self.cached_messages = data["messages"]
            if "users" in data:
                self.cached_users = data["users"]
            if "channels" in data:
                self.cached_channels = data["channels"]
            logging.info("Loaded bot_cache")

    @discord.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.type == discord.ChannelType.private:
            return

        self.cache_message(message)

    @discord.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        try:

            changes = []

            cached = self.get_cached_message(payload.message_id)
            if not cached:
                return
            cached_author = self.get_cached_user(cached["authorID"])
            if not cached_author:
                return

            if "bot" in cached_author and cached_author["bot"]:
                return

            fetched = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)

            if cached["content"] != fetched.content:
                changes.append(("Content", cached["content"], fetched.content))

            changes.extend(compare_embeds(cached["embeds"], fetched.embeds))

            if len(changes) == 0:
                return

            log_channel = self.bot.get_channel(int(CHANNEL_MODERATION))

            await log_channel.send(embed=discord.Embed(
                title="Message Edited",
                color=discord.Color.yellow(),
                description="A message has been edited.",
                fields=[*[discord.EmbedField(name=i[0], value=f"{i[1]} -> {i[2]}") for i in changes],
                        discord.EmbedField(name="Link", value=f"[Jump]({fetched.jump_url})")]
            ))

            self.update_cached_message(fetched)
        except Exception as e:
            sentry_sdk.capture_exception(e)

    @discord.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        try:
            cached = self.get_cached_message(payload.message_id)

            if not cached:
                return

            cached_author = self.get_cached_user(cached["authorID"])
            if not cached_author:
                return
            if "bot" in cached_author and cached_author["bot"]:
                return

            log_channel = self.bot.get_channel(int(CHANNEL_MODERATION))

            await log_channel.send(embed=discord.Embed(
                title="Message Deleted",
                color=discord.Color.red(),
                description="A message has been deleted.\n\n"
                            f"{cached['content']}",
                fields=[
                    discord.EmbedField(name="Link", value=f"[Jump](https://discord.com/channels/{payload.guild_id}/{payload.channel_id}/{payload.message_id})")
                ]
            ))
        except Exception as e:
            sentry_sdk.capture_exception(e)
