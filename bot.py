import json
import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from config import BOT_TOKEN, CHANNELS, ADMIN_IDS
from decorators import require_subscription
from texts import welcome_text, referral_link, subscription_text
from utils import check_subs, get_not_subscribed_channels

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

DATA_FILE = "database.json"
REKLAMA_FILE = "media/media.mp4"
REKLAMA_TEXT_FILE = "media/media.txt"
admin_state = {}

os.makedirs(os.path.dirname(REKLAMA_FILE), exist_ok=True)

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_user(data, user_id):
    return data.get(str(user_id), {"referrals": [], "joined": False, "bonus_level": 0})

def load_reklama_text():
    if not os.path.exists(REKLAMA_TEXT_FILE):
        return "🎬 Reklama videosi"
    try:
        with open(REKLAMA_TEXT_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "🎬 Reklama videosi"

async def send_secret_channel(user_id: int, level: int):
    messages = {
        1: "🎉 Siz 20+ do‘st chaqirdingiz! Maxfiy guruh havolasi:",
        2: "🚀 Siz 40+ do‘st chaqirdingiz! Yangi maxfiy guruh havolasi:",
        3: "🔥 60+ referal! Maxfiy guruh havolasi:",
        4: "👑 80+ do‘st! VIP guruh havolasi:"
    }

    links = {
        1: "https://t.me/+GMBcIQpSD-JjZDFi",
        2: "https://t.me/+S-vPexKC4GY4YmMy",
        3: "https://t.me/+N40A5zIrXHliOTUy",
        4: "https://t.me/+nmKGx-BUullkMGQy"
    }

    if level in messages and level in links:
        await bot.send_message(
            chat_id=user_id,
            text=f"{messages[level]}\n{links[level]}"
        )

@dp.message_handler(lambda msg: msg.text == "🔐 Maxfiy kanal")
@require_subscription(bot)
async def secret_group_access(message: types.Message):
    user_id = str(message.from_user.id)
    data = load_data()

    if user_id not in data:
        await message.answer("Iltimos, /start tugmasini bosing.")
        return

    referrals = len(set(data[user_id]["referrals"]))
    bonus_level = data[user_id].get("bonus_level", 0)

    secret_links = {
        1: {
            "link": "https://t.me/+GMBcIQpSD-JjZDFi",
            "text": "🎉 Tabriklaymiz! Siz 20+ do‘st chaqirdingiz. Maxfiy guruh havolasi 👇"
        },
        2: {
            "link": "https://t.me/+S-vPexKC4GY4YmMy",
            "text": "🚀 Siz 40+ do‘st chaqirdingiz! Ikkinchi maxfiy guruh havolasi:"
        },
        3: {
            "link": "https://t.me/+N40A5zIrXHliOTUy",
            "text": "🔥 60+ referal! Uchinchi bosqich havolasi mana bu yerda:"
        },
        4: {
            "link": "https://t.me/+nmKGx-BUullkMGQy",
            "text": "👑 Siz TOP darajaga yetdingiz! Maxsus VIP havola:"
        }
    }

    response = ""
    for level in range(1, 5):
        if referrals >= level * 20 and bonus_level >= level:
            key = f"link_sent_{level}"
            if not data[user_id].get(key, False):
                data[user_id][key] = True
                response += f"{secret_links[level]['text']}\n{secret_links[level]['link']}\n\n"

    if response:
        await message.answer(response.strip())
        save_data(data)
    else:
        await message.answer("❗ Hozircha sizga maxfiy guruhlar uchun havola mavjud emas. Do‘stlaringizni taklif qilishda davom eting!")


@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.full_name
    data = load_data()

    if str(user_id) not in data:
        data[str(user_id)] = {"referrals": [], "joined": False, "bonus_level": 0}

    not_joined = await get_not_subscribed_channels(bot, user_id)

    if not_joined:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("✅ Tekshirish")

        text = "❗ Quyidagi kanallarga obuna bo‘ling:\n\n"
        for ch in not_joined:
            text += f"🔸 <a href='https://t.me/{ch['username'][1:]}'>{ch['title']}</a>\n"

        inline = types.InlineKeyboardMarkup()
        for ch in not_joined:
            inline.add(types.InlineKeyboardButton(
                text=f"📲 {ch['title']}",
                url=f"https://t.me/{ch['username'][1:]}"
            ))

        await message.answer(text, reply_markup=inline, parse_mode="HTML", disable_web_page_preview=True)
        await message.answer("Obuna bo‘lgach, «✅ Tekshirish» tugmasini bosing 👇", reply_markup=markup)
        return

    data[str(user_id)]["joined"] = True

    args = message.get_args()
    if args and args != str(user_id):
        ref_id = str(args)
        if ref_id in data and str(user_id) != ref_id:
            ref_user = data[ref_id]
            if str(user_id) not in ref_user["referrals"]:
                ref_user["referrals"].append(str(user_id))
                referral_count = len(set(ref_user["referrals"]))
                old_level = ref_user.get("bonus_level", 0)
                new_level = referral_count // 20
                if new_level > old_level:
                    ref_user["bonus_level"] = new_level
                    await send_secret_channel(int(ref_id), new_level)

    save_data(data)

    try:
        reklama_text = load_reklama_text()
        with open(REKLAMA_FILE, "rb") as video_file:
            await bot.send_video(
                chat_id=message.chat.id,
                video=video_file,
                caption=reklama_text,
                parse_mode="Markdown"
            )
    except Exception as e:
        logging.error(f"Video yuborishda xatolik: {e}")
        await message.answer("🎬 Reklama videosi")

    ref_count = len(data[str(user_id)]["referrals"])
    btns = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btns.add("🔗 Referal havolam", "📊 Reyting", "🎁 Sovrinlar")
    btns.add("🔐 Maxfiy kanal")
    if str(user_id) in ADMIN_IDS:
        btns.add("📢 Xabar yuborish", "🎬 Reklamani o‘zgartirish")

    await message.answer(welcome_text(username, ref_count), reply_markup=btns)

@dp.message_handler(lambda msg: msg.text == "✅ Tekshirish")
async def recheck_subs(message: types.Message):
    user_id = message.from_user.id
    not_joined = await get_not_subscribed_channels(bot, user_id)

    if not_joined:
        text = "🚫 Hali ham quyidagi kanallarga obuna emassiz:\n\n"
        for ch in not_joined:
            text += f"🔸 <a href='https://t.me/{ch['username'][1:]}'>{ch['title']}</a>\n"
        text += "\nIltimos, barcha kanallarga obuna bo‘ling va qaytadan «✅ Tekshirish» tugmasini bosing."

        inline = types.InlineKeyboardMarkup()
        for ch in not_joined:
            inline.add(types.InlineKeyboardButton(
                text=f"📲 {ch['title']}",
                url=f"https://t.me/{ch['username'][1:]}"
            ))

        await message.answer(text, reply_markup=inline, parse_mode="HTML", disable_web_page_preview=True)
    else:
        await start_handler(message)

@dp.callback_query_handler(lambda c: c.data == "check_subs")
async def check_subscriptions(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.full_name
    data = load_data()

    if not await check_subs(user_id):
        await callback.answer("❌ Hali hamma kanallarga obuna bo‘lmadingiz", show_alert=True)
        return

    data[str(user_id)]["joined"] = True
    save_data(data)
    ref_count = len(data[str(user_id)]["referrals"])

    btns = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btns.add("🔗 Referal havolam", "📊 Reyting", "🎁 Sovrinlar")
    if str(user_id) in ADMIN_IDS:
        btns.add("📢 Xabar yuborish", "🎬 Reklamani o‘zgartirish")
    
    await callback.message.answer(welcome_text(username, ref_count), reply_markup=btns)
    await callback.answer()

    try:
        reklama_text = load_reklama_text()
        with open(REKLAMA_FILE, "rb") as video_file:
            await bot.send_video(
                chat_id=user_id,
                video=video_file,
                caption=reklama_text,
                parse_mode="Markdown"
            )
    except Exception as e:
        logging.error(f"Video send error: {e}")
        await bot.send_message(user_id, "🎬 Reklama videosi")

@dp.message_handler(lambda m: m.text == "🔗 Referal havolam")
@require_subscription(bot)
async def send_referral_link(message: types.Message):
    user_id = message.from_user.id
    link = referral_link(user_id)
    await message.answer(
        f"🔗 Sizning referal havolangiz:\n{link}\n\n"
        "Har 20 ta qo'shilgan referal uchun yopiq 1 oylik bepul guruh linki beriladi!"
    )

@dp.message_handler(lambda m: m.text == "🎁 Sovrinlar")
@require_subscription(bot)
async def show_rewards(message: types.Message):
    user_id = message.from_user.id
    data = load_data()
    user_data = data.get(str(user_id), {})

    if not user_data.get("joined", False):
        await message.answer("❌ Sovrinlar bo‘limiga kirish uchun barcha kanallarga obuna bo‘ling!")
        return

    ref_count = len(user_data.get("referrals", []))
    text = (
        "🎁 <b>Mavjud sovrinlar:</b>\n\n"
        "🥇 1-o'rin uchun sovg'a — planshet\n"
        "🥈 2- o'rin uchu sovg'a — kitob o’qiydigan qurilma\n"
        "🥉 3- o'rin uchun sovg'a — 300.000 so’m pul\n"
        "🏅 Qolgan 20 ta o'rin sohiblari uchun — 50.000 so'm miqdordagi pul mukofoti\n\n"
        f"👥 Siz hozircha {ref_count} ta do‘st taklif qilgansiz."
    )
    await message.answer(text)

@dp.message_handler(lambda m: m.text == "🔐 Maxfiy kanal")
@require_subscription(bot)
async def secret_group_access(message: types.Message):
    if not await check_subs(message.from_user.id):
        await message.answer("❗ Iltimos, barcha kanallarga obuna bo‘ling!")
        return
        link = referral_link(message.from_user.id)
        await message.answer(
            f"🔗 Sizning referal havolangiz:\n{link}\n\n"
                "Har 20 ta qo'shilgan referal uchun yopiq 1 oylik bepul guruh linki beriladi!"
        )

@dp.message_handler(lambda m: m.text == "📊 Reyting")
@require_subscription(bot)
async def show_rating(message: types.Message):
    data = load_data()
    users = [(uid, info) for uid, info in data.items() if info.get("joined")]
    users.sort(key=lambda x: len(x[1]["referrals"]), reverse=True)
    
    text = "🏆 <b>Top Referallar:</b>\n\n"
    for i, (uid, info) in enumerate(users[:10], 1):
        try:
            user = await bot.get_chat(int(uid))
            name = user.full_name
            username = f"@{user.username}" if user.username else "Foydalanuvchi"
            count = len(info["referrals"])
            text += f"{i}. {name} ({username}) - {count} ta\n"
        except:
            text += f"{i}. [Noma'lum foydalanuvchi] - {len(info['referrals'])} ta\n"
    
    current_uid = str(message.from_user.id)
    if current_uid in data:
        user_data = data[current_uid]
        if user_data.get("joined"):
            user_pos = next((i for i, (uid, _) in enumerate(users, 1) if uid == current_uid), None)
            if user_pos and user_pos > 10:
                count = len(user_data["referrals"])
                text += f"\n📌 Sizning o'rningiz: {user_pos} ({count} ta)"
    
    await message.answer(text)

@dp.message_handler(lambda m: m.text == "📢 Xabar yuborish")
async def admin_start_broadcast(message: types.Message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return await message.answer("⛔ Siz admin emassiz.")
    
    admin_state[message.from_user.id] = "broadcast"
    await message.answer("✉️ Yuboriladigan xabar matnini yuboring:")

@dp.message_handler(lambda m: admin_state.get(m.from_user.id) == "broadcast", content_types=types.ContentTypes.ANY)
async def send_broadcast(message: types.Message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return
    
    data = load_data()
    count = 0
    errors = 0
    total = len(data)
    
    status_msg = await message.answer(f"⏳ Xabar yuborilmoqda... 0/{total}")
    
    for i, (uid, _) in enumerate(data.items(), 1):
        if i % 10 == 0:
            await status_msg.edit_text(f"⏳ Xabar yuborilmoqda... {i}/{total}")
            await asyncio.sleep(0.5)
        
        try:
            await message.send_copy(int(uid))
            count += 1
        except Exception as e:
            errors += 1
            logging.error(f"Broadcast error to {uid}: {e}")
        
        await asyncio.sleep(0.05)
    
    admin_state.pop(message.from_user.id, None)
    await status_msg.delete()
    await message.answer(
        f"✅ Xabar yuborish yakunlandi!\n"
        f"• Muvaffaqiyatli: {count}\n"
        f"• Xatolar: {errors}\n"
        f"• Jami: {total}"
    )

@dp.message_handler(lambda m: m.text == "🎬 Reklamani o‘zgartirish")
async def ask_reklama(message: types.Message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return await message.answer("⛔ Siz admin emassiz.")
    
    admin_state[message.from_user.id] = "reklama_video"
    await message.answer("📹 Yangi reklama videosini yuboring (video + caption):")

@dp.message_handler(content_types=types.ContentType.VIDEO, state="*")
async def handle_reklama_video(message: types.Message):
    if admin_state.get(message.from_user.id) != "reklama_video":
        return
    
    try:
        await message.video.download(destination_file=REKLAMA_FILE)
        
        if message.caption:
            with open(REKLAMA_TEXT_FILE, "w", encoding="utf-8") as f:
                f.write(message.caption)
        elif os.path.exists(REKLAMA_TEXT_FILE):
            os.remove(REKLAMA_TEXT_FILE)
        
        await message.answer("✅ Reklama video yangilandi!")
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")
    finally:
        admin_state.pop(message.from_user.id, None)

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("bot.log"),
            logging.StreamHandler()
        ]
    )
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())