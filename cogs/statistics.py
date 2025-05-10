import datetime
import re

import discord
import sentry_sdk

from constants import OWNER
from util.storage import get_data


def calculate_basic_analytics(data: dict) -> tuple[int, int, int]:
    """
    Calculate basic analytics statistics
    :return: Numbers total message count, meow count and :3 count :3
    """

    # Total messages
    total = len(data["messages"])

    # Meows and :3's

    meows = 0
    colon_threes = 0

    for i in data["messages"]:
        for j in re.finditer(r":(3+)", i["content"].lower()):
            meows = meows + len(j[1])

        for j in re.finditer(r"(m[mraeow]{3,}|nya+)", i["content"].lower()):
            colon_threes = colon_threes + len(j[1])

    return total, meows, colon_threes

def group_last_7_days(data: dict):
    """
    Calculate most 3 days active in the last week
    :param data:
    :return:
    """

    final_data = {}

    for i in data["messages"]:
        created_at = datetime.datetime.fromisoformat(i["sentat"])

        if datetime.datetime.now(datetime.timezone.utc) - created_at > datetime.timedelta(days=7):
            continue

        date_str = created_at.strftime("%Y-%m-%d")

        if date_str not in final_data:
            final_data[date_str] = 0

        final_data[date_str] += 1

    final_data = set(final_data.items())
    final_data = sorted(final_data, key=lambda x: x[1], reverse=True)

    output_str = ""

    for k, v in final_data[:3]:
        output_str += f"{k}: {v}\n"

    return output_str

class ServerStatistics(discord.Cog):
    def __init__(self, bot: discord.Bot):
        super().__init__()
        self.bot = bot

    @discord.slash_command(name="statistics", description="Shows server statistics")
    async def statistics(self, ctx: discord.ApplicationContext):
        try:
            if ctx.user.id != int(OWNER):
                await ctx.respond("You are not authorized to use this command :3", ephemeral=True)
                return

            data = get_data("bot_cache")

            total, meows, colon_threes = calculate_basic_analytics(data)
            activity = group_last_7_days(data)

            await ctx.respond(f"""
# {total} messages :3
Meows: {meows}, :3's {colon_threes}

## Activity:

{activity}""")
        except Exception as e:
            await ctx.respond("An error occured UwU", ephemeral=True)
            sentry_sdk.capture_exception(e)
