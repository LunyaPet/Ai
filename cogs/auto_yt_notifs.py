import asyncio
import datetime

import discord
import sentry_sdk
import yt_dlp
from discord.ext import tasks

from constants import CHANNEL_NEW_VIDEOS, ROLE_VIDEOS, YT_LINK
from util.storage import get_data, set_data


async def get_all_latest_post_info():
    try:
        ydl = yt_dlp.YoutubeDL()

        info = ydl.extract_info(f"{YT_LINK}/videos", download=False, process=False)
        i = 0
        output = []
        for j in info["entries"]:
            output.append({
                "id": j["id"],
                "title": j["title"],
                "description": j["description"],
                "thumbnail": j["thumbnails"][-1]["url"],
                "view_count": j["view_count"]
            })

            i = i + 1
            if i > 10:
                break

        return output
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return []


class AutoYouTubeNotifications(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.Cog.listener()
    async def on_ready(self):
        existing_data = get_data("yt_notifications")

        # Check if the module was initialized
        if existing_data.get("initialized", False):
            self.check_latest_videos.start()
            return

        existing_data["initialized"] = True
        existing_data["posted_ids"] = []
        existing_data["posted_data"] = []

        posts = await get_all_latest_post_info()
        existing_data["posted_ids"].extend([i["id"] for i in posts])
        existing_data["posted_data"].extend(posts)

        set_data("yt_notifications", existing_data)

        self.check_latest_videos.start()

    @tasks.loop(hours=1)
    async def check_latest_videos(self):

        try:
            existing_data = get_data("yt_notifications")

            posts = await get_all_latest_post_info()

            channel = self.bot.get_channel(int(CHANNEL_NEW_VIDEOS))

            for i in posts:
                if i["id"] in existing_data["posted_ids"]:
                    continue

                emb = discord.Embed(
                    title=i["title"],
                    description=i["description"],
                    color=discord.Color.red(),
                    url=f"https://youtube.com/watch?v={i['id']}",
                    image=i["thumbnail"],
                    fields=[
                        discord.EmbedField(name="Views", value=i["view_count"], inline=True)
                    ]
                )

                asyncio.get_event_loop().create_task(
                    channel.send(f"<@&{ROLE_VIDEOS}> mldchan posted a new video~!\nClick the title of the embed or click this link~ https://youtube.com/watch?v={i['id']}", embed=emb)
                )

                existing_data["posted_ids"].append(i["id"])
                existing_data["posted_data"].append(i)

            # Go through the history of messages and update the embeds based on information fetched
            async for msg in channel.history():
                for i in posts:
                    if i["id"] in msg.content:
                        # Update the embed
                        emb = discord.Embed(
                            title=i["title"],
                            description=i["description"],
                            color=discord.Color.red(),
                            url=f"https://youtube.com/watch?v={i['id']}",
                            image=i["thumbnail"],
                            fields=[
                                discord.EmbedField(name="Views", value=i["view_count"], inline=True)
                            ]
                        )


                        asyncio.get_event_loop().create_task(msg.edit(embed=emb))

            set_data("yt_notifications", existing_data)
        except Exception as e:
            sentry_sdk.capture_exception(e)

