"""from os import environ

from nextcord.ext.commands import Context, check


STAFF = int(environ["STAFF_ROLE"])


def is_staff():
    async def predicate(ctx: Context) -> bool:
        if not ctx.guild: return False

        return STAFF in ctx.author._roles  # type: ignore
    return check(predicate)"""

def has_auto_perms():
    """If a mod has automod perms"""
    pass

def bypass_auto_mod():
    """If user is able to bypass automod"""
    pass

def is_helper():
    """If user is a helper"""
    pass

def is_staff():
    """If user is staff"""
    pass