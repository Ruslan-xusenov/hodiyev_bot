from functools import wraps
from aiogram import types
from utils import get_not_subscribed_channels

def require_subscription(bot):
    def decorator(handler):
        @wraps(handler)
        async def wrapper(message: types.Message, *args, **kwargs):
            user_id = message.from_user.id
            not_joined = await get_not_subscribed_channels(bot, user_id)

            if not_joined:
                text = "❗ Iltimos, quyidagi kanallarga obuna bo‘ling:\n\n"
                for ch in not_joined:
                    text += f"🔸 <a href='https://t.me/{ch.username}'>{ch.title}</a>\n"

                markup = types.InlineKeyboardMarkup()
                for ch in not_joined:
                    markup.add(types.InlineKeyboardButton(
                        text=f"📲 {ch.title}",
                        url=f"https://t.me/{ch.username}"
                    ))
                markup.add(types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_subs"))

                await message.answer(text, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=True)
                return

            return await handler(message, *args, **kwargs)
        return wrapper
    return decorator
