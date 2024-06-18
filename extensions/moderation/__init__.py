from .moderation import Moderation


class Mod(
    Moderation,
):
    pass

async def setup(bot):
    await bot.add_cog(Mod(bot))