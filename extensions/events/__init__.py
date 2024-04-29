from .listener import Listener

class Events(
    Listener
):
    pass

async def setup(bot):
    await bot.add_cog(Events(bot))