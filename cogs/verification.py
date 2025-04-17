import asyncio
import os
import time

import discord
import sentry_sdk
from discord.ext import tasks

from util.notifications import notifications_to_roles
from util.pronouns import validate_pronouns, get_sets_for_pronouns, get_roles_for_pronouns
from util.storage import set_data, get_data

ROLE_VERIFIED = os.getenv("ROLES_VERIFIED")
if ROLE_VERIFIED is None:
    print("WARNING: The ROLES_VERIFIED environment variable is not set. Verifying will not work properly. Please set it to the ID of the Verified role.")


class Verification(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

        if not os.path.exists("data"):
            os.mkdir("data")

        if not os.path.exists("data/verification"):
            os.mkdir("data/verification")

    @discord.Cog.listener()
    async def on_ready(self):
        print("✨ Verification Cog is all ready~! ˚₊· ͟͟͞͞➳❥")

        self.bot.add_view(StartVerificationButton())
        self.bot.add_view(FinishVerificationButton())

        self.delete_verification_channels.start()

    @tasks.loop(minutes=1)
    async def delete_verification_channels(self):
        try:
            channel_delete_queue = get_data("verification/channel_delete_queue")
            if not 'queue' in channel_delete_queue:
                return

            for i in range(len(channel_delete_queue['queue'])):
                if channel_delete_queue['queue'][i]['time'] < int(time.time()):
                    channel = self.bot.get_channel(channel_delete_queue['queue'][i]['channel_id'])
                    if channel is not None:
                        await channel.delete()
        except Exception as e:
            sentry_sdk.capture_exception(e)

    @discord.Cog.listener()
    async def on_message(self, message: discord.Message):
        try:
            if message.author.bot:
                return

            existing_data = get_data(f"verification/{message.author.id}")
            if 'state' not in existing_data:
                return
            if 'channel' not in existing_data:
                return
            if existing_data['channel'] != message.channel.id:
                return

            if existing_data['state'] == 'pronouns':
                if not validate_pronouns(message.content):
                    await message.reply(
                        "Eep! I don't understand those pronouns... Could you try again, please? (✿◕‿◕✿) ˚₊· ͟͟͞͞➳❥")
                    return

                pronouns = get_sets_for_pronouns(message.content)
                await message.reply(f"Yay~! I've set your pronouns to {', '.join(pronouns)}! ⋆｡˚˛♡")

                existing_data['pronouns'] = pronouns
                existing_data['state'] = 'notifications'
                set_data(f"verification/{message.author.id}", existing_data)

                await message.channel.send("# 2. ✨ Notifications ✨ ˚₊· ͟͟͞͞➳❥\n\n"
                                           "Now let's set up which notifs you wanna get, okay~? ˚₊· ͟͟͞͞➳❥💖\n"
                                           "Use `+name` to *subscribe* or `-name` to *unsubscribe*. For example: `+videos` to get video updates! 🎥\n"
                                           "You can mix and match! Like: `+videos +server +streams` all at once ✨｡˚\n"
                                           "When you're ready, type `next` to continue~! ˚₊· ͟͟͞͞➳❥\n\n"
                                           "## 💌 Available notifications: ⋆｡˚˛♡\n"
                                           "- `videos`: New YouTube videos by mldchan! 📹\n"
                                           "- `streams`: Live streams on YouTube! 🎤\n"
                                           "- `tiktok`: Cute posts on TikTok! 🎶\n"
                                           "- `fedi`: Fediverse posts from mldchan~ 🐾\n"
                                           "- `server`: Updates for this server! 🏠")

            elif existing_data['state'] == 'notifications':
                if 'notifications' not in existing_data:
                    existing_data['notifications'] = []
                    set_data(f"verification/{message.author.id}", existing_data)

                if message.content.lower() == 'next':
                    await message.reply(
                        f"Kyaa~! You’re signed up for {', '.join(existing_data['notifications'])}! 🐱‍👤 ⋆｡˚˛♡")
                    await message.channel.send("All set with your notifs, thank youuu! 💖\n\n"
                                               "One last thing, cutie~ Please read our rules to keep our space safe and cozy! ˚₊· ͟͟͞͞➳❥\n"
                                               "Here's the tl;dr: Be kind, be respectful, and keep it sweet. No meanies allowed! 😤\n\n"
                                               "If you agree, click the green button below to finish up~ 🍵✨",
                                               view=FinishVerificationButton())
                    existing_data['state'] = 'rules'
                    set_data(f"verification/{message.author.id}", existing_data)
                    return

                for i in ['videos', 'streams', 'tiktok', 'fedi', 'server']:
                    if f'+{i}' in message.content and i not in existing_data['notifications']:
                        existing_data['notifications'].append(i)
                    if f'-{i}' in message.content and i in existing_data['notifications']:
                        existing_data['notifications'].remove(i)

                if len(existing_data['notifications']) == 0:
                    await message.reply("Oki doki! You're not subscribed to any notifs yet. (´• ω •`) ⋆｡˚˛♡")
                else:
                    await message.reply(
                        f"So far so good~ You're getting: {', '.join(existing_data['notifications'])}! 🧸⋆｡˚˛♡")

                set_data(f"verification/{message.author.id}", existing_data)
        except Exception as e:
            sentry_sdk.capture_exception(e)


class StartVerificationButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.primary, custom_id="start_verify")
    async def start_verification(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            # Verified member check

            if any([i.id == int(ROLE_VERIFIED) for i in interaction.user.roles]):
                await interaction.respond("You're already verified!", ephemeral=True)
                return

            # Existing channel check
            existing_data = get_data(f"verification/{interaction.user.id}")
            if 'channel' in existing_data:
                existing_channel = interaction.guild.get_channel(existing_data['channel'])
                if existing_channel is None:
                    set_data(f"verification/{interaction.user.id}", {})
                    await interaction.respond("An error occurred. Please try again!", ephemeral=True)
                    return

                await interaction.respond(
                    f"You have already begun the verification process! Please check {existing_channel[0].mention}!",
                    ephemeral=True)
                return

            group_id = os.getenv("VERIFICATION_GROUP_ID")
            group = interaction.guild.get_channel(int(group_id))

            if group is None:
                await interaction.response.send_message("The verification group has not been set up yet.",
                                                        ephemeral=True)
                return

            channel = await interaction.guild.create_text_channel(name=f"verification-{interaction.user.name}",
                                                                  category=group,
                                                                  topic=f"Verification channel for {interaction.user.display_name}",
                                                                  overwrites={
                                                                      interaction.user: discord.PermissionOverwrite(
                                                                          view_channel=True, send_messages=True),
                                                                      interaction.guild.default_role: discord.PermissionOverwrite(
                                                                          view_channel=False)})

            await channel.send(
                f"{interaction.user.mention} Haiiii~! (*≧ω≦) ⋆｡˚˛♡ Welcome to mldchan's cozy Discord~!\n\n"
                "I'm Ai (愛), the maid of this lovely server~ Let's get you all comfy and verified! ˚₊· ͟͟͞͞➳❥\n"
                "Just answer a few questions and we’ll be done in no time! 💕")
            pronouns_msg = await channel.send("# 1. 🌸 Pronouns 🌸 ⋆｡˚˛♡\n\n"
                                              "Please tell me your pronouns so others can address you properly~! ˚₊· ͟͟͞͞➳❥\n\n"
                                              "You can type something like `they/them`, a single word like `she`, or even `name` if you'd prefer people to use your name!\n\n"
                                              "Supported pronouns: `he/him`, `she/her`, `they/them`, `one/ones`, `it/its`, `name`, `she/it`, `he/it` 🌈")

            set_data(f"verification/{interaction.user.id}",
                     {"state": "pronouns", "channel": channel.id, "pronouns_msg": pronouns_msg.id})

            await interaction.respond(
                f"Please check {channel.mention} to begin your verification journey~! (*≧▽≦) ˚₊· ͟͟͞͞➳❥",
                ephemeral=True)
        except Exception as e:
            sentry_sdk.capture_exception(e)


class FinishVerificationButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="I agree to the rules and let's go!", style=discord.ButtonStyle.success,
                       custom_id="finish_verify")
    async def finish_verification(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            existing_data = get_data(f"verification/{interaction.user.id}")
            if 'channel' not in existing_data:
                await interaction.response.send_message("You haven't started the verification process yet!",
                                                        ephemeral=True)
                return

            if existing_data["state"] != "rules":
                await interaction.response.send_message("You are already verified!",
                                                        ephemeral=True)
                return

            # Assign pronoun roles
            for role_id in [get_roles_for_pronouns(i) for i in existing_data['pronouns']]:
                role = interaction.guild.get_role(int(role_id))
                if role is None:
                    continue

                await  interaction.user.add_roles(role)

            # Assign notification roles
            for notification in notifications_to_roles(existing_data['notifications']):
                role = interaction.guild.get_role(int(notification))
                if role is None:
                    continue

                await interaction.user.add_roles(role)

            # Assign the "Verified" role
            verified_role = interaction.guild.get_role(int(ROLE_VERIFIED))
            await interaction.user.add_roles(verified_role)

            # Respond
            await interaction.respond("Yayyy~! 🎉 You're officially part of our community now! 💕 ˚₊· ͟͟͞͞➳❥\n"
                                      "- Come say hi in <#general>! 🌟\n"
                                      "- Customize your roles in <#roles>! 🎀\n"
                                      "- Drop fun suggestions in <#suggestions>! 💡\n"
                                      "We're so happy to have you here~! 🫶 (｡♥‿♥｡) ⋆｡˚˛♡")

            # Add the channel to the deletion queue (10 minutes)

            channel_delete_queue = get_data("verification/channel_delete_queue")
            if not 'queue' in channel_delete_queue:
                channel_delete_queue['queue'] = []

            channel_delete_queue['queue'].append({'channel_id': existing_data['channel'], 'time': int(time.time()) + 600})

            set_data("verification/channel_delete_queue", channel_delete_queue)

            existing_data['state'] = 'finished'
            set_data(f"verification/{interaction.user.id}", existing_data)
        except Exception as e:
            sentry_sdk.capture_exception(e)
