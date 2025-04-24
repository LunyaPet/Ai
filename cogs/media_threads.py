import discord

from constants import CHANNEL_MEDIA

class MediaThreads(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        if str(msg.channel.id) != CHANNEL_MEDIA.strip():
            return

        if len(msg.attachments) == 0:
            return

        if not all([i.content_type.startswith("image") or i.content_type.startswith("video") for i in msg.attachments]):
            return

        msg_in_length = f"{msg.author.display_name}'s media" + (f": {msg.content}" if len(msg.content.strip()) > 0 else "")
        if len(msg_in_length) > 61:
            msg_in_length = msg_in_length[:61] + "..."

        thr = await msg.create_thread(name=msg_in_length)
        await thr.send(content="˚₊· ͟͟͞➳❥ Haii~ I created this thread on your post and all comments on this media should go here~ ˚ ༘♡ ⋆｡˚")
