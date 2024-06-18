from discord.ext import commands
from discord import app_commands


async def check_guild_permissions(ctx: commands.Context, perms: dict[str, bool], *, check=all):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    if ctx.guild is None:
        return False

    resolved = ctx.author.guild_permissions
    return check(getattr(resolved, name, None) == value for name, value in perms.items())


def hybrid_permissions_check(**perms: bool):
    async def pred(ctx: commands.Context):
        return await check_guild_permissions(ctx, perms)

    def decorator(func):
        commands.check(pred)(func)
        app_commands.default_permissions(**perms)(func)
        return func

    return decorator

def is_admin():
    return hybrid_permissions_check(administrator=True)