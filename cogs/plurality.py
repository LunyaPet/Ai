import asyncio
import os.path
import random
import shutil

import discord
import sentry_sdk

from util.storage import get_data, set_data


def get_actual_author_for_msg(msg_id: str):
    existing_data = get_data("plurality/sent_messages")
    for k, v in existing_data.items():
        if msg_id in v:
            return k

    return None


class Plurality(discord.Cog):
    def __init__(self, bot: discord.Bot):
        super().__init__()
        self.bot = bot

    plurality_group = discord.SlashCommandGroup(name="plurality", description="Set up plurality")

    @plurality_group.command()
    async def set_character(self,
                            ctx: discord.ApplicationContext,
                            name: discord.Option(str, description="Name of your character", max_length=64),
                            pronouns: discord.Option(str, description="Pronouns", max_length=20, min_length=2,
                                                     default=""),
                            trigger: discord.Option(str,
                                                    description="Trigger keyword at the start of the word you're typing",
                                                    min_length=1, max_length=10, default=""),
                            description: discord.Option(str, description="Describe your character", default=""),
                            avatar: discord.Option(str,
                                                   description="Set the avatar URL. Post an image somewhere (DM's of the bot) and copy the URL",
                                                   default="")):
        try:
            # At least one parameter
            if pronouns.strip() == "" and trigger.strip() == "" and description.strip() == "" and avatar.strip() == "":
                await ctx.respond("At least one parameter pleaseee :(", ephemeral=True)
                return

            # Create a new character
            existing_data = get_data(f"plurality/{ctx.user.id}")
            if 'characters' not in existing_data:
                existing_data['characters'] = {}

            existing = name in existing_data['characters']

            if not existing and (name.strip() == "" or pronouns.strip() == "" or trigger.strip() == ""):
                await ctx.respond(
                    "Specify required parameters name, pronouns and trigger when creating a new character :3",
                    ephemeral=True)
                return

            if avatar.strip() == "":
                if name not in existing_data['characters'].keys():
                    avatar = ""
                else:
                    avatar = existing_data['characters'][name]['avatar']

            existing_data['characters'][name] = {
                'pronouns': pronouns if pronouns.strip() != "" else existing_data['characters'][name]['pronouns'],
                'description': description if description.strip() != "" else existing_data['characters'][name][
                    'description'],
                'trigger_kwd': trigger if trigger.strip() != "" else existing_data['characters'][name]['trigger_kwd'],
                'avatar': avatar
            }

            set_data(f"plurality/{ctx.user.id}", existing_data)
            await ctx.respond(
                f"Character was updated :3".strip() if existing else f"Character was created :3".strip(),
                ephemeral=True)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await ctx.respond("An error occurred. An alert was sent to the owner and she'll fix it.", ephemeral=True)

    @plurality_group.command()
    async def del_character(self, ctx: discord.ApplicationContext, name: str):
        try:
            # Delete a character
            existing_data = get_data(f"plurality/{ctx.user.id}")
            if 'characters' not in existing_data:
                existing_data['characters'] = {}

            if name not in existing_data['characters'].keys():
                await ctx.respond("Character does not exist.", ephemeral=True)
                return

            del existing_data['characters'][name]

            set_data(f"plurality/{ctx.user.id}", existing_data)
            await ctx.respond("Character was deleted.", ephemeral=True)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await ctx.respond("An error occurred. An alert was sent to the owner and she'll fix it.", ephemeral=True)

    @plurality_group.command()
    async def list_characters(self, ctx: discord.ApplicationContext):
        try:
            # List characters for a user
            existing_data = get_data(f"plurality/{ctx.user.id}")
            if 'characters' not in existing_data:
                existing_data['characters'] = {}

            embeds = []

            for (name, props) in existing_data['characters'].items():
                embeds.append(discord.Embed(
                    author=discord.EmbedAuthor(
                        name=name,
                        icon_url=props['avatar']
                    ),
                    description=props['description'],
                    fields=[
                        discord.EmbedField(name="Pronouns", value=props['pronouns'], inline=True),
                        discord.EmbedField(name="Keyword", value=props['trigger_kwd'], inline=True)
                    ],
                    color=random.choice(
                        [discord.Color.red(), discord.Color.blurple(), discord.Color.blue(), discord.Color.green(),
                         discord.Color.og_blurple(), discord.Color.yellow(), discord.Color.orange(),
                         discord.Color.nitro_pink()])
                ))

            await ctx.respond(f"# {ctx.user.display_name}'s System", embeds=embeds, ephemeral=True)
        except Exception as e:
            sentry_sdk.capture_exception(e)

    @plurality_group.command()
    async def set_default(self, ctx: discord.ApplicationContext, name: discord.Option(str, description="Name of the character to set as default. Empty to disable.") = ""):
        try:
            existing_data = get_data(f"plurality/{ctx.user.id}")

            # Special case: No value entered, unset value
            if name.strip() == "":
                del existing_data['defaultCharacter']
                set_data(f"plurality/{ctx.user.id}", existing_data)
                await ctx.respond("The default character was unset.", ephemeral=True)
                return

            if 'characters' not in existing_data:
                existing_data['characters'] = {}

            if name not in existing_data['characters']:
                await ctx.respond("No such character exists!", ephemeral=True)
                return

            existing_data['defaultCharacter'] = name

            set_data(f"plurality/{ctx.user.id}", existing_data)
            await ctx.respond(f"The default character was set to {name}.", ephemeral=True)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            await ctx.respond("An error occurred. An alert was sent to the owner and she'll fix it.", ephemeral=True)

    @discord.Cog.listener()
    async def on_message(self, message: discord.Message):
        try:
            # Read settings for plurality
            existing_settings = get_data(f"plurality/{message.author.id}")
            if 'characters' not in existing_settings or 'id' not in existing_settings:
                return

            for k, v in existing_settings['characters'].items():
                if message.content.startswith(v['trigger_kwd']):
                    # Proxy as trigger keyword character
                    await self.proxy(message, k, v)
                    return

            if 'defaultCharacter' in existing_settings:
                # Proxy as default character
                await self.proxy(message, existing_settings['defaultCharacter'],
                                 existing_settings['characters'][existing_settings['defaultCharacter']])
                return

            # Do nothing when nothing
        except Exception as e:
            sentry_sdk.capture_exception(e)

    webhook_store = {}

    async def proxy(self, message: discord.Message, name: str, character_data: dict):
        try:
            # Save all media
            if not os.path.exists("temp"):
                os.mkdir("temp")

            for i in message.attachments:
                await i.save(f"temp/{i.filename}")

            # Get first webhook from cache

            if str(message.channel.id) in self.webhook_store:
                webhook = self.webhook_store[str(message.channel.id)]
            else:
                webhooks = await message.channel.webhooks()
                if len(webhooks) == 0:
                    webhook = await message.channel.create_webhook(name="MsgProxy")
                    self.webhook_store[str(message.channel.id)] = webhook
                else:
                    webhook = webhooks[0]
                    self.webhook_store[str(message.channel.id)] = webhook

            # Remove the keyword
            clean_message = message.content
            if clean_message.startswith(character_data['trigger_kwd']):
                clean_message = " ".join(clean_message.split(" ")[len(character_data['trigger_kwd'].split(" ")):])

            # Attach reply information
            reply_info = ""
            if message.reference is not None and message.reference.resolved is not None:
                if isinstance(message.reference, discord.DeletedReferencedMessage):
                    reply_info = "RE: *Deleted message*\n"
                elif isinstance(message.reference.resolved, discord.Message):
                    reply_info = f"RE: {message.reference.resolved.jump_url}\n"

            clean_message = f"{reply_info}{clean_message}".strip()

            # Proxy the message
            await webhook.send(clean_message, username=name,
                               files=[discord.File(f"temp/{i.filename}", i.filename) for i in message.attachments],
                               poll=message.poll if message.poll is not None else None,
                               avatar_url=character_data['avatar'] if 'avatar' in character_data and
                                                                      character_data['avatar'] is not None and
                                                                      character_data['avatar'].strip() != "" else None)

            asyncio.get_event_loop().create_task(self.query_last_webhook_msg(message),
                                                 name=f"Plurality Fetch Message {message.id}")

            # Delete the temp folder
            shutil.rmtree("temp")

            # Delete the original
            asyncio.get_running_loop().create_task(message.delete(), name=f"Plurality Delete Message {message.id}")
            asyncio.get_running_loop().create_task(self.dm_replied_to_user(message),
                                                   name=f"Plurality Send Reply Notification {message.id}")
        except Exception as e:
            sentry_sdk.capture_exception(e)

    async def dm_replied_to_user(self, message):
        # DM the user who was involved in replying
        if message.reference is not None and message.reference.resolved is not None:
            if isinstance(message.reference, discord.DeletedReferencedMessage):
                return

            actual_author_id = get_actual_author_for_msg(str(message.reference.resolved.id))

            if actual_author_id is None:
                return

            actual_author = message.guild.get_member(int(actual_author_id))

            if actual_author is None:
                return

            await actual_author.send(embed=discord.Embed(
                title="Your character was mentioned",
                description="One of your characters has been mentioned inside a message",
                fields=[
                    discord.EmbedField(name="Message", value=f"[jump]({message.jump_url})")
                ],
                color=discord.Color.blurple(),
                footer=discord.EmbedFooter(text="mldchan's Ai")
            ))

    async def query_last_webhook_msg(self, message):
        # Query the first non-user message
        async for i in message.channel.history():
            if i.webhook_id is not None:
                sent_messages = get_data("plurality/sent_messages")

                if str(message.author.id) not in sent_messages:
                    sent_messages[str(message.author.id)] = []

                sent_messages[str(message.author.id)].append(str(i.id))

                set_data("plurality/sent_messages", sent_messages)
                break

    @discord.message_command(name="[Admin]Lookup Message")
    async def mod_lookup_message(self, ctx: discord.ApplicationContext, message: discord.Message):
        try:
            if not ctx.user.guild_permissions.manage_permissions:
                await ctx.respond("You do not have the appropriate permissions to invade others' privacy.",
                                  ephemeral=True)
                return

            data = get_data("plurality/sent_messages")

            for k, v in data.items():
                print(str(message.id), v, str(message.author.id) in v, k)
                if str(message.id) in v:
                    await ctx.respond(f"The user who sent this message is <@{k}>.", ephemeral=True)
                    break
            else:
                await ctx.respond("User/Message not found.", ephemeral=True)
        except Exception as e:
            await ctx.respond("An error occurred.", ephemeral=True)
            sentry_sdk.capture_exception(e)
