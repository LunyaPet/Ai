import asyncio
import logging

import discord
import sentry_sdk

from constants import GUILD, CHANNEL_MODERATION
from util.storage import set_data, get_data


def compare_embeds(cached, embeds: list[discord.Embed]):
    cached: list[discord.Embed] = [discord.Embed.from_dict(i) for i in cached]

    differences: list[tuple[str, str, str]] = []

    for (i, v) in enumerate(zip(cached, embeds)):
        if v[0].title != v[1].title:
            differences.append((f"Embed {i + 1} Title", v[0].title, v[1].title))
        if v[0].description != v[1].description:
            differences.append((f"Embed {i + 1} Description", v[0].description, v[1].description))
        if v[0].author.name != v[1].author.name:
            differences.append((f"Embed {i + 1} Author", v[0].author.name, v[1].author.name))

        for (j, w) in enumerate(zip(v[0].fields, v[1].fields)):
            if w[0].name != w[1].name:
                differences.append((f"Embed {i + 1} Field {j + 1} Name", w[0].name, w[1].name))
            if w[0].value != w[1].value:
                differences.append((f"Embed {i + 1} Field {j + 1} Value", w[0].value, w[1].value))

    return differences


class InitCache(discord.Cog):
    def __init__(self, bot: discord.Bot):
        super().__init__()
        self.bot = bot
        self.cached_messages: list[dict] = []
        self.cached_users: list[dict] = []
        self.cached_channels: list[dict] = []
        self.cached_emojis: list[dict] = []
        self.load()

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
            logging.info(f"Created cache for %d messages and %d users", len(self.cached_messages), len(self.cached_users))
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
                "reactions": [{
                    "emojiname": i.emoji.name,
                    "emojiid": i.emoji.id,
                    "count": i.count
                } for i in message.reactions],
                "embeds": [i.to_dict() for i in message.embeds],
                "sentat": message.created_at.isoformat(timespec="minutes")
            })

        if not any(i['id'] == message.author.id for i in self.cached_users):
            self.cached_users.append({
                "id": message.author.id,
                "username": message.author.name,
                "displayname": message.author.display_name,
                "avatar": message.author.display_avatar.url
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
                fields=[discord.EmbedField(name=i[0], value=f"{i[1]} -> {i[2]}") for i in changes]
            ))
        except Exception as e:
            sentry_sdk.capture_exception(e)

