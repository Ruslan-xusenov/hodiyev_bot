from config import CHANNELS

async def check_subs(bot, user_id):
    for channel in CHANNELS:
        try:
            username = channel["username"]
            member = await bot.get_chat_member(username, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception:
            return False
    return True

async def get_not_subscribed_channels(bot, user_id):
    not_joined = []

    for channel in CHANNELS:
        try:
            username = channel["username"]
            member = await bot.get_chat_member(username, user_id)
            if member.status in ["left", "kicked"]:
                title = channel.get("title") or (await bot.get_chat(username)).title
                not_joined.append({
                    "username": username,
                    "title": title
                })
        except Exception:
            not_joined.append({
                "username": channel.get("username"),
                "title": channel.get("title") or channel.get("username")
            })

    return not_joined