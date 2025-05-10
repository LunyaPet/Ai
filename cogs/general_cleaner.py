import datetime

import discord

from constants import CHANNEL_GENERAL, CHANNEL_MEDIA

RESET_TIMER = 1  # minutes

class GeneralCleaner(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    data = {}

    @discord.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Check if the message was sent in #general
        if str(message.channel.id) != CHANNEL_GENERAL.strip():
            return

        # Check for media
        is_media = len(message.attachments) > 0
        if not is_media:
            return

        # Init user if not initalized
        if message.author.id not in self.data:
            self.data[message.author.id] = {
                'expiry_date': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=RESET_TIMER),
                'attachments_sent': 0,
                'sent': False
            }

        # Reset if after expiry date
        if self.data[message.author.id]['expiry_date'] < datetime.datetime.now(datetime.timezone.utc):
            self.data[message.author.id]['attachments_sent'] = 0
            self.data[message.author.id]['sent'] = False

        # Increment user
        self.data[message.author.id]['attachments_sent'] += 1
        self.data[message.author.id]['expiry_date'] = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=RESET_TIMER)

        if self.data[message.author.id]['attachments_sent'] > 2 and not self.data[message.author.id]['sent']:
            # If exceeded, remind the user that the media channel exists
            self.data[message.author.id]['sent'] = True
            await message.reply(f"˚₊· ͟͟͞➳❥ Please use the <#{CHANNEL_MEDIA}> channel for posting media~ Thank you! ˚ ༘♡ ⋆｡˚")
