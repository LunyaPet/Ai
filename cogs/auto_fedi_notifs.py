import asyncio

import aiohttp
import discord
from discord.ext import tasks

from constants import CHANNEL_NEW_FEDI, ROLE_FEDI, FEDI_INSTANCE, FEDI_USER_ID
from util.storage import get_data, set_data


async def get_latest_posts():
    async with aiohttp.ClientSession() as session:
        async with await session.post(f"https://{FEDI_INSTANCE}/api/users/notes",
                                      json={"limit": 10, "userId": FEDI_USER_ID}) as resp:
            js = await resp.json()

            posts = js
            posts = [i for i in posts if i['cw'] is None or len(i['cw']) == 0]         # posts without cw
            posts = [i for i in posts if i['visibility'] == "public"]                  # public posts only
            posts = [i for i in posts if 'reply' not in i or i['reply'] is None]       # no replies
            posts = [i for i in posts if 'renote' not in i or i['renote'] is None]     # no boosts

            return [i["id"] for i in posts]

    return []


class AutoFediNotifications(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.Cog.listener()
    async def on_ready(self):
        # Fetch existing data
        existing_data = get_data("fedi_notifications")

        # Check if the module was initialized
        if existing_data.get("initialized", False):
            self.fetch_new_posts.start()
            return

        existing_data["initialized"] = True
        existing_data["posted_posts"] = []

        posts = await get_latest_posts()
        existing_data["posted_posts"].extend(posts)

        set_data("fedi_notifications", existing_data)

        self.fetch_new_posts.start()

    @tasks.loop(minutes=1)
    async def fetch_new_posts(self):
        # Fetch new fediverse posts
        posts = await get_latest_posts()

        channel = self.bot.get_channel(int(CHANNEL_NEW_FEDI))
        if channel is None:
            return

        existing_data = get_data("fedi_notifications")

        for i in posts:
            if i in existing_data["posted_posts"]:
                continue

            asyncio.get_event_loop().create_task(
                channel.send(
                    f"<@&{ROLE_FEDI}> mldchan posted a new note on fedi~! Go check it out~ https://{FEDI_INSTANCE}/notes/{i}")
            )

            existing_data["posted_posts"].append(i)

        set_data("fedi_notifications", existing_data)
