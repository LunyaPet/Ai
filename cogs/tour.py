import discord

from constants import CHANNEL_ROLES, CHANNEL_GENERAL, CHANNEL_MEDIA, CHANNEL_MEMES, CHANNEL_SUGGESTIONS


def get_message(stage: str, user_mention: str):
    if stage == "roles":
        return f"{user_mention}\n# ˚₊‧꒰🎀 Roles ˚₊‧꒱\nHere you can configure your cute lil' roles~! Pick a gender identity, sexual orientation, and romantical orientation role~ or change your existing sparkle~roles! (｡♥‿♥｡)"
    elif stage == "general":
        return f"{user_mention}\n# ˚₊‧꒰💬 General ˚₊‧꒱\nThis is your cozy chat space with all the sweet members~ Say haii to everyone and spread the love~! ₊˚ʚ♡ɞ˚₊"
    elif stage == "other_channels":
        return (f"{user_mention}\n"
                f"# ˚₊‧꒰🌸 Other Channels ˚₊‧꒱\n"
                f"Don’t forget to explore the rest of this sparkly server~!! ✧˖°\nWe’ve got:\n"
                f"- <#{CHANNEL_MEDIA}> — Post your lovely media creations here~! ✨\n"
                f"- <#{CHANNEL_MEMES}> — Got memes? Share them here and giggle together~! (≧◡≦)\n"
                f"- 🎮 The gaming section has tons of channels for mldchan’s fav games~ Come play & share screenshots too!\n"
                f"- 💡 Got an idea? Drop server suggestions into <#{CHANNEL_SUGGESTIONS}>~!")

    return f"{user_mention} - Invalid stage: {stage}"

class TourView(discord.ui.View):
    def __init__(self, stage: str, user_id: str):
        super().__init__(timeout=60, disable_on_timeout=False)

        self.stage = stage
        self.user_id = user_id

    async def on_timeout(self) -> None:
        await self.message.delete()

    # Previous button
    @discord.ui.button(label="<-", style=discord.ButtonStyle.primary)
    async def go_back(self, button: discord.ui.Button, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.respond("This is not your tour", ephemeral=True)
            return

        # Handle depending on the stage
        if self.stage == "roles":
            await interaction.respond("You are at the beginning", ephemeral=True)
        elif self.stage == "general":
            await interaction.respond(f"<#{CHANNEL_ROLES}>", ephemeral=True)
            await interaction.guild.get_channel(int(CHANNEL_ROLES)).send(get_message("roles", interaction.user.mention), view=TourView("roles", str(interaction.user.id)))
            self.stop()
            await interaction.message.delete()
        elif self.stage == "other_channels":
            await interaction.guild.get_channel(int(CHANNEL_GENERAL)).send(get_message("general", interaction.user.mention), view=TourView("general", str(interaction.user.id)))
            self.stop()
            await interaction.message.delete()

    # Next button
    @discord.ui.button(label="->", style=discord.ButtonStyle.primary)
    async def go_forward(self, button: discord.ui.Button, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.respond("This is not your tour", ephemeral=True)
            return

        # Handle depending on the stage
        if self.stage == "roles":
            await interaction.respond(f"<#{CHANNEL_GENERAL}>", ephemeral=True)
            await interaction.guild.get_channel(int(CHANNEL_GENERAL)).send(get_message("general", interaction.user.mention), view=TourView("general", str(interaction.user.id)))
            self.stop()
            await interaction.message.delete()
        elif self.stage == "general":
            await interaction.guild.get_channel(int(CHANNEL_GENERAL)).send(get_message("other_channels", interaction.user.mention), view=TourView("other_channels", str(interaction.user.id)))
            self.stop()
            await interaction.message.delete()
        elif self.stage == "other_channels":
            await interaction.respond("This is the end of the tour! Thanks for taking it!", ephemeral=True)
            self.stop()
            await interaction.message.delete()

    # Skip button
    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary)
    async def skip_tour(self, button: discord.ui.Button, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.respond("This is not your tour", ephemeral=True)
            return

        await interaction.respond("Alright, tour skipped~", ephemeral=True)
        self.stop()
        await interaction.message.delete()
