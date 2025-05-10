import asyncio

import discord
import sentry_sdk
import yt_dlp
from discord.ext import tasks

from constants import TT_LINK, ROLE_TIKTOK, CHANNEL_NEW_TIKTOK
from util.storage import get_data, set_data


async def get_all_latest_post_info():
    try:
        ydl = yt_dlp.YoutubeDL()

        info = ydl.extract_info(TT_LINK, download=False, process=False)
        i = 0
        output = []
        for j in info["entries"]:
            output.append({
                "id": j["id"],
                "title": j["title"],
                "description": j["description"],
                "thumbnail": j["thumbnails"][0]["url"],
                "view_count": j["view_count"],
                "comment_count": j["comment_count"],
                "like_count": j["like_count"],
                "url": j["url"]
            })

            i = i + 1
            if i > 10:
                break

        return output
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return []


class AutoTikTokNotifications(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.Cog.listener()
    async def on_ready(self):
        existing_data = get_data("tt_notifications")

        # Check if the module was initialized
        if existing_data.get("initialized", False):
            self.check_latest_videos.start()
            return

        existing_data["initialized"] = True
        existing_data["posted_ids"] = []
        existing_data["posted_data"] = []
        existing_data["counter"] = 0

        posts = await get_all_latest_post_info()
        existing_data["posted_ids"].extend([i["id"] for i in posts])
        existing_data["posted_data"].extend(posts)

        set_data("tt_notifications", existing_data)

        self.check_latest_videos.start()

    @tasks.loop(minutes=5)
    async def check_latest_videos(self):

        try:
            existing_data = get_data("tt_notifications")

            posts = await get_all_latest_post_info()

            channel = self.bot.get_channel(int(CHANNEL_NEW_TIKTOK))

            for i in posts:
                if i["id"] in existing_data["posted_ids"]:
                    continue

                existing_data["counter"] = existing_data["counter"] + 1

                emb = discord.Embed(
                    title="mldchan just posted a video!",
                    description=f'{i["title"]}\n\n{i["description"]}',
                    color=discord.Color.from_rgb(32, 170, 176) if existing_data["counter"] % 2 == 0 else discord.Color.from_rgb(236, 0, 70),
                    url=i["url"],
                    image=i["thumbnail"],
                    fields=[
                        discord.EmbedField(name="Views", value=i["view_count"], inline=True),
                        discord.EmbedField(name="Likes", value=i["like_count"], inline=True),
                        discord.EmbedField(name="Comments", value=i["comment_count"], inline=True)
                    ]
                )
                asyncio.get_event_loop().create_task(
                    channel.send(f"<@&{ROLE_TIKTOK}> mldchan posted a new video~!\nClick the title of the embed or click this link~ <{i['url']}>", embed=emb)
                )
                existing_data["posted_ids"].append(i["id"])
                existing_data["posted_data"].append(i)

            async for msg in channel.history():
                for i in posts:
                    if i["id"] in msg.content:
                        # Update the embed
                        emb = discord.Embed(
                            title="mldchan just posted a video!",
                            description=f'{i["title"]}\n\n{i["description"]}',
                            color=discord.Color.from_rgb(32, 170, 176) if existing_data[
                                                                              "counter"] % 2 == 0 else discord.Color.from_rgb(
                                236, 0, 70),
                            url=i["url"],
                            image=i["thumbnail"],
                            fields=[
                                discord.EmbedField(name="Views", value=i["view_count"], inline=True),
                                discord.EmbedField(name="Likes", value=i["like_count"], inline=True),
                                discord.EmbedField(name="Comments", value=i["comment_count"], inline=True)
                            ]
                        )



                        asyncio.get_event_loop().create_task(
                            msg.edit(embed=emb)
                        )

            set_data("tt_notifications", existing_data)
        except Exception as e:
            sentry_sdk.capture_exception(e)

