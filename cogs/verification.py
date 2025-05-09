import os
import os
import time

import discord
import sentry_sdk
from discord.ext import tasks

from cogs.tour import get_message, TourView
from constants import ROLE_VERIFIED, CHANNEL_GENERAL, CHANNEL_ROLES, CHANNEL_SUGGESTIONS, VERIFICATION_GROUP_ID, \
    CHANNEL_MODERATION, ROLE_MOD, CHANNEL_RULES
from util.notifications import notifications_to_roles
from util.pronouns import validate_pronouns, get_sets_for_pronouns, get_roles_for_pronouns
from util.quarantine import is_member_in_quarantine
from util.storage import set_data, get_data, delete_data


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
        self.bot.add_view(HandleQuarantineButton())
        self.bot.add_view(NotificationsView("0"))

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
                        delete_data(f"quarantine_state/{channel.id}")
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
                        "I don't understand those pronouns... Could you try again, please? (✿◕‿◕✿) ˚₊· ͟͟͞͞➳❥\n"
                        "Make sure your pronuns are slash separated, e.g. `she/they` will give you `she/her` and `they/them`!")
                    return

                pronouns = get_sets_for_pronouns(message.content)
                await message.reply(f"Yay~! I've set your pronouns to {', '.join(pronouns)}! ⋆｡˚˛♡")

                existing_data['pronouns'] = pronouns
                existing_data['state'] = 'notifications'
                set_data(f"verification/{message.author.id}", existing_data)

                await message.channel.send("# 2. ✨ Notifications ✨ ˚₊· ͟͟͞͞➳❥\n\n"
                                           "Now pick which notifs you wanna get, okay~? ˚₊· ͟͟͞͞➳❥💖\n"
                                           "When you're ready, click the `Next` button to continue~! ˚₊· ͟͟͞͞➳❥\n\n",
                                           view=NotificationsView(str(message.author.id)))
        except Exception as e:
            sentry_sdk.capture_exception(e)

    @discord.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        try:
            # Existing channel check
            existing_data = get_data(f"verification/{member.id}")
            if existing_data != {}:
                delete_data(f"verification/{member.id}")

            # Delete channel if exist
            existing_channel = member.guild.get_channel(existing_data['channel'])
            if existing_channel is None:
                return

            await existing_channel.delete()
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
                    f"You have already begun the verification process! Please check {existing_channel.mention}!",
                    ephemeral=True)
                return

            group_id = VERIFICATION_GROUP_ID
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
                                              "Please tell me your pronouns so others can address you properly~! ˚₊· ͟͟͞͞➳❥\n"
                                              "You can type something like `they/them`, a single word like `she`, or even `name` if you'd prefer people to use your name!🌈")

            set_data(f"verification/{interaction.user.id}",
                     {"state": "pronouns", "channel": channel.id, "pronouns_msg": pronouns_msg.id})

            await interaction.respond(
                f"Please check {channel.mention} to begin your verification journey~! (*≧▽≦) ˚₊· ͟͟͞͞➳❥",
                ephemeral=True)
        except Exception as e:
            sentry_sdk.capture_exception(e)


class NotificationsView(discord.ui.View):
    def __init__(self, user_id: str):
        super().__init__(timeout=None)

        self.clear_items()
        self.generate_buttons(user_id)

    def generate_buttons(self, user_id: str):
        try:
            existing_data = get_data(f"verification/{user_id}")

            if 'notifications' not in existing_data:
                existing_data['notifications'] = []
                set_data(f"verification/{user_id}", existing_data)

            for (key, text) in [('videos', 'Videos'), ('streams', 'Streams'), ('tiktok', 'TikTok'),
                                ('fedi', 'Notes on the Fediverse'), ('server', 'Discord Server Updates')]:
                if key in existing_data['notifications']:
                    button = discord.ui.Button(label=text, style=discord.ButtonStyle.green,
                                               custom_id='disable_notifs_' + key)
                    button.callback = self.disable_notification
                    self.add_item(button)
                else:
                    button = discord.ui.Button(label=text, style=discord.ButtonStyle.red,
                                               custom_id='enable_notifs_' + key)
                    button.callback = self.enable_notification
                    self.add_item(button)

            enable_all_button = discord.ui.Button(label="Enable all notifications", style=discord.ButtonStyle.gray,
                                                  custom_id='notifs_enable_all')
            enable_all_button.callback = self.enable_all_notifications
            self.add_item(enable_all_button)

            disable_all_button = discord.ui.Button(label="Disable all notifications", style=discord.ButtonStyle.gray,
                                                   custom_id='notifs_disable_all')
            disable_all_button.callback = self.disable_all_notifications
            self.add_item(disable_all_button)

            recommended_button = discord.ui.Button(label="Select Recommended", style=discord.ButtonStyle.primary,
                                                   custom_id='notifs_select_recommended')
            recommended_button.callback = self.recommended_notifications
            self.add_item(recommended_button)

            next_button = discord.ui.Button(label='Next', style=discord.ButtonStyle.primary, custom_id='notifs_next')
            next_button.callback = self.next_button
            self.add_item(next_button)
        except Exception as e:
            sentry_sdk.capture_exception(e)

    async def disable_notification(self, interaction: discord.Interaction):
        try:
            existing_data = get_data(f"verification/{interaction.user.id}")

            if existing_data['state'] != 'notifications':
                await interaction.respond(
                    f"heehee, you can't change the notifications right now, pwease use the <#{CHANNEL_ROLES}> channel to do that, okay? >///< ",
                    ephemeral=True)
                return

            existing_data['notifications'].remove(interaction.custom_id[15:])

            set_data(f'verification/{interaction.user.id}', existing_data)

            self.clear_items()
            self.generate_buttons(str(interaction.user.id))

            await interaction.edit(view=self)
        except Exception as e:
            sentry_sdk.capture_exception(e)

    async def enable_notification(self, interaction: discord.Interaction):
        try:
            existing_data = get_data(f"verification/{interaction.user.id}")

            if existing_data['state'] != 'notifications':
                await interaction.respond(
                    f"heehee, you can't change the notifications right now, pwease use the <#{CHANNEL_ROLES}> channel to do that, okay? >///< ",
                    ephemeral=True)
                return

            existing_data['notifications'].append(interaction.custom_id[14:])

            set_data(f'verification/{interaction.user.id}', existing_data)

            self.clear_items()
            self.generate_buttons(str(interaction.user.id))

            await interaction.edit(view=self)
        except Exception as e:
            sentry_sdk.capture_exception(e)

    async def enable_all_notifications(self, interaction: discord.Interaction):
        try:
            existing_data = get_data(f"verification/{interaction.user.id}")

            if existing_data['state'] != 'notifications':
                await interaction.respond(
                    f"heehee, you can't change the notifications right now, pwease use the <#{CHANNEL_ROLES}> channel to do that, okay? >///< ",
                    ephemeral=True)
                return

            for i in ['videos', 'streams', 'tiktok', 'fedi', 'server']:
                if i not in existing_data['notifications']:
                    existing_data['notifications'].append(i)

            set_data(f'verification/{interaction.user.id}', existing_data)

            self.clear_items()
            self.generate_buttons(str(interaction.user.id))

            await interaction.edit(view=self)
        except Exception as e:
            sentry_sdk.capture_exception(e)

    async def disable_all_notifications(self, interaction: discord.Interaction):
        try:
            existing_data = get_data(f"verification/{interaction.user.id}")

            if existing_data['state'] != 'notifications':
                await interaction.respond(
                    f"heehee, you can't change the notifications right now, pwease use the <#{CHANNEL_ROLES}> channel to do that, okay? >///< ",
                    ephemeral=True)
                return

            for i in ['videos', 'streams', 'tiktok', 'fedi', 'server']:
                if i in existing_data['notifications']:
                    existing_data['notifications'].remove(i)

            set_data(f'verification/{interaction.user.id}', existing_data)

            self.clear_items()
            self.generate_buttons(str(interaction.user.id))

            await interaction.edit(view=self)
        except Exception as e:
            sentry_sdk.capture_exception(e)

    async def recommended_notifications(self, interaction: discord.Interaction):
        try:
            existing_data = get_data(f"verification/{interaction.user.id}")

            if existing_data['state'] != 'notifications':
                await interaction.respond(
                    f"heehee, you can't change the notifications right now, pwease use the <#{CHANNEL_ROLES}> channel to do that, okay? >///< ",
                    ephemeral=True)
                return

            existing_data['notifications'] = ['videos', 'streams', 'tiktok', 'server']

            set_data(f'verification/{interaction.user.id}', existing_data)

            self.clear_items()
            self.generate_buttons(str(interaction.user.id))

            await interaction.edit(view=self)
        except Exception as e:
            sentry_sdk.capture_exception(e)

    async def next_button(self, interaction: discord.Interaction):
        try:
            existing_data = get_data(f"verification/{interaction.user.id}")

            if existing_data['state'] != 'notifications':
                await interaction.respond(
                    f"heehee, you can't change the notifications right now, pwease use the <#{CHANNEL_ROLES}> channel to do that, okay? >///< ",
                    ephemeral=True)
                return

            if is_member_in_quarantine(interaction.user.id):
                message_1 = await interaction.respond("Oops! You were quarantined!\n"
                                                      "Please write a simple about you in here and please wait until an admin manually verifies you."
                                                      "We are sorry for the inconvinence, but we want to keep our members safe.",
                                                      view=HandleQuarantineButton())

                existing_data['state'] = 'quarantine'
                set_data(f"verification/{interaction.user.id}", existing_data)
                set_data(f"quarantine_state/{message_1.channel.id}", {
                    'member_id': interaction.user.id
                })

                log_channel = interaction.guild.get_channel(int(CHANNEL_MODERATION))
                if log_channel is None:
                    return

                await log_channel.send(embed=discord.Embed(title="Action Required",
                                                           description=f"A member in {interaction.channel.mention} was quarantined! Please check their introduction once they write one!",
                                                           color=discord.Color.red()))
            else:
                await interaction.respond("All set with your notifs, thank youuu! 💖\n"
                                          f"Please take a look at the <#{CHANNEL_RULES}>, and agree to them and you're all set~! Thank you!",
                                          view=FinishVerificationButton())
                existing_data['state'] = 'rules'
                set_data(f"verification/{interaction.user.id}", existing_data)
        except Exception as e:
            await interaction.respond("Something went wrong :(", ephemeral=True)
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
                await interaction.respond("You haven't started the verification process yet!",
                                                        ephemeral=True)
                return

            if existing_data["state"] != "rules":
                await interaction.respond("You are already verified!", ephemeral=True)
                return

            # Respond
            await interaction.respond("Yayyy~! 🎉 You're officially part of our community now! 💕 ˚₊· ͟͟͞͞➳❥\n"
                                      "We're so happy to have you here~! 🫶 (｡♥‿♥｡) ⋆｡˚˛♡\n"
                                      "Feel free to take the server tour now~ ❤️️", view=StartTourView())

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
            
            # Ping member in General and send welcome message in there
            general = interaction.guild.get_channel(int(CHANNEL_GENERAL))
            await general.send(f"Welcome {interaction.user.mention} to the server~!")

            # Add the channel to the deletion queue (10 minutes)
            channel_delete_queue = get_data("verification/channel_delete_queue")
            if not 'queue' in channel_delete_queue:
                channel_delete_queue['queue'] = []

            channel_delete_queue['queue'].append(
                {'channel_id': existing_data['channel'], 'time': int(time.time()) + 600})

            set_data("verification/channel_delete_queue", channel_delete_queue)

            existing_data['state'] = 'finished'
            set_data(f"verification/{interaction.user.id}", existing_data)
        except Exception as e:
            sentry_sdk.capture_exception(e)


class StartTourView(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Start Server Tour", style=discord.ButtonStyle.primary)
    async def start_tour(self, button: discord.ui.Button, interaction: discord.Interaction):
        existing_data = get_data(f"verification/{interaction.user.id}")

        if 'tour' in existing_data and existing_data['tour'] == True:
            await interaction.respond("You already took the tour. You cannot take it again.", ephemeral=True)
            return

        existing_data['tour'] = True
        set_data(f"verification/{interaction.user.id}", existing_data)

        await interaction.guild.get_channel(int(CHANNEL_ROLES)).send(get_message("roles", interaction.user.mention), view=TourView("roles", str(interaction.user.id)))
        await interaction.respond(
            f"You should have received a ping in <#{CHANNEL_ROLES}>! Take a look in there, the bot will take you through a small tour of the server.",
            ephemeral=True)


class HandleQuarantineButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Unquarantine User", style=discord.ButtonStyle.success, custom_id="unquarantine")
    async def unquarantine_user(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            # Get state
            quarantine_data = get_data(f"quarantine_state/{interaction.channel_id}")
            if quarantine_data == {}:
                await interaction.respond("Not found", ephemeral=True)
                return

            # Mod check
            if int(ROLE_MOD) not in [i.id for i in interaction.user.roles]:
                await interaction.respond("Insufficient permissions", ephemeral=True)
                return

                # Load data
            existing_data = get_data(f"verification/{quarantine_data['member_id']}")

            # Check verification state
            if existing_data['state'] != 'quarantine':
                await interaction.respond('Invalid state!', ephemeral=True)
                return

            # Set state
            existing_data['state'] = 'finished'
            set_data(f"verification/{quarantine_data['member_id']}", existing_data)

            # Send message
            await interaction.channel.send(f"<@{quarantine_data['member_id']}>\n\n"
                                           f"Your quarantine request was approved, thank youuu! 💖\n\n"
                                           "One last thing, cutie~ Please read our rules to keep our space safe and cozy! ˚₊· ͟͟͞͞➳❥\n"
                                           "Here's the tl;dr: Be kind, be respectful, and keep it sweet. No meanies allowed! 😤\n\n"
                                           "If you agree, click the green button below to finish up~ 🍵✨",
                                           view=FinishVerificationButton())

            # Respond to admin
            await interaction.respond("Unquarantined the user succesfull!", ephemeral=True)
            self.stop()
        except Exception as e:
            await interaction.respond("Something went wrong!", ephemeral=True)
            sentry_sdk.capture_exception(e)

    @discord.ui.button(label="Ban User...", style=discord.ButtonStyle.danger, custom_id="ban_user")
    async def ban_user(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            # Get state
            quarantine_data = get_data(f"quarantine_state/{interaction.channel_id}")
            if quarantine_data == {}:
                await interaction.respond("Not found", ephemeral=True)
                return

            # Mod check
            if int(ROLE_MOD) not in [i.id for i in interaction.user.roles]:
                await interaction.respond("Insufficient permissions", ephemeral=True)
                return

                # Load data
            existing_data = get_data(f"verification/{quarantine_data['member_id']}")

            # Check verification state
            if existing_data['state'] != 'quarantine':
                await interaction.respond('Invalid state!', ephemeral=True)
                return

                # Delete data
            delete_data(f"verification/{quarantine_data['member_id']}")

            # Respond to admin
            await interaction.respond(f"User was banned!", ephemeral=True)

            # Ban user
            user = interaction.guild.get_member(quarantine_data['member_id'])
            await user.ban(delete_message_seconds=7 * 24 * 3600, reason="Quarantine")
        except Exception as e:
            await interaction.respond("Something went wrong!", ephemeral=True)
            sentry_sdk.capture_exception(e)
