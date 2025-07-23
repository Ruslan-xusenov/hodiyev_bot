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
                inline = types.InlineKeyboardMarkup()

                for ch in not_joined:
                    username = ch.get("username", "").lstrip("@")
                    title = ch.get("title", "Kanal")
                    text += f"🔸 <a href='https://t.me/{username}'>{title}</a>\n"
                    inline.add(types.InlineKeyboardButton(
                        text=f"📲 {title}",
                        url=f"https://t.me/{username}"
                    ))

                # Pastki menyu (reply keyboard)
                reply = types.ReplyKeyboardMarkup(resize_keyboard=True)
                reply.add("✅ Tekshirish")

                # Inline tugmalar bilan kanal ro‘yxati
                await message.answer(
                    text,
                    reply_markup=inline,
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )

                # Pastki reply tugma bilan qo‘shimcha xabar
                await message.answer(
                    "Obuna bo‘lgach, pastdagi «✅ Tekshirish» tugmasini bosing 👇",
                    reply_markup=reply
                )
                return

            return await handler(message, *args, **kwargs)
        return wrapper
    return decorator