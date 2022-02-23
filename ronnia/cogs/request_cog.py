import attr
from ronnia.bots.twitch_bot import TwitchBot
from twitchio.ext import commands


@attr.s
class RangeInput(object):
    range_low = attr.ib(converter=float)
    range_high = attr.ib(converter=float)


class RequestCog(commands.Cog):
    def __init__(self, bot: TwitchBot):
        self.bot = bot

    @commands.command(name="echo", aliases=["feedback"])
    async def toggle_feedback(self, ctx):

        self.bot.config['Feedback'] = not self.bot.config['Feedback']
        new_echo_status = self.bot.config['Feedback']

        if new_echo_status is False:
            await ctx.send("Disabled feedback message after requests!")
        else:
            await ctx.send("Enabled feedback message after requests!")

    @commands.command(name="sub-only")
    async def sub_only(self, ctx):
        self.bot.config['SubOnly'] = not self.bot.config['SubOnly']
        new_sub_only_status = self.bot.config['SubOnly']

        if new_sub_only_status:
            await ctx.send(
                f"Enabled sub-only mode on the channel! Type {self.bot.main_prefix}sub-only again to disable.")
        else:
            await ctx.send(
                f"Disabled sub-only mode on the channel. Type {self.bot.main_prefix}sub-only again to enable.")


def prepare(bot: TwitchBot):
    # Load our cog with this module...
    bot.add_cog(RequestCog(bot))
