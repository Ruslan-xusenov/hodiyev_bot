from config import CHANNELS

async def check_subs(bot, user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(channel["username"], user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception:
            return False
    return True

async def get_not_subscribed_channels(bot, user_id):
    not_joined = []
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(channel["username"], user_id)
            if member.status not in ("member", "administrator", "creator"):
                not_joined.append(channel)
        except Exception:
            not_joined.append(channel)
    return not_joined