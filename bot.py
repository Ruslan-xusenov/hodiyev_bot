import json
import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ChatInviteLink
from aiogram.utils import executor
from config import BOT_TOKEN, CHANNELS, ADMIN_IDS
from decorators import require_subscription
from texts import welcome_text, referral_link, subscription_text
from utils import check_subs, get_not_subscribed_channels
from datetime import datetime, timedelta


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

@dp.message_handler(commands=["get_id"], commands_prefix="/")
async def get_channel_id(message: types.Message):
    if message.chat.type in ["channel"]:
        await message.reply(f"Kanal ID: <code>{message.chat.id}</code>", parse_mode="HTML")
    else:
        await message.reply("❗ Iltimos, bu komandani kanal ichida yuboring (bot admin bo’lishi lozim).")

CHANNEL_LINKS = {
    1: {"id": -1001234567890, "fallback": "https://t.me/+GMBcIQpSD-JjZDFi"},
    2: {"id": -1001234567891, "fallback": "https://t.me/+S-vPexKC4GY4YmMy"},
    3: {"id": -1001234567892, "fallback": "https://t.me/+N40A5zIrXHliOTUy"},
    4: {"id": -1001234567893, "fallback": "https://t.me/+nmKGx-BUullkMGQy"},
}

async def send_secret_channel(user_id: int, max_level: int):
    for level in range(1, max_level + 1):
        channel_info = CHANNEL_LINKS.get(level)
        if not channel_info:
            await bot.send_message(user_id, f"❌ {level}-bosqich uchun kanal topilmadi.")
            continue

        channel_id = channel_info["id"]
        fallback_link = channel_info["fallback"]

        try:
            invite_link: ChatInviteLink = await bot.create_chat_invite_link(
                chat_id=channel_id,
                member_limit=1,
                expire_date=datetime.now() + timedelta(days=1),
                name=f"user-{user_id}-level-{level}"
            )
            link = invite_link.invite_link
        except Exception as e:
            logging.exception(f"❌ {level}-bosqich havola yaratishda xatolik:")
            link = fallback_link

        # Bosiladigan link formatda yuboriladi
        await bot.send_message(
            user_id,
            f"🎁 {level}-bosqich maxfiy kanal: [Kanalga qo'shilish uchun shu yerni bosing]({link})",
            parse_mode="Markdown"
        )


@dp.message_handler(lambda m: m.text == "🔐 Bonus kanallar")
@require_subscription(bot)
async def secret_group_access(message: types.Message):
    user_id = message.from_user.id
    data = load_data()

    user_data = data.get(str(user_id), {})
    referrals = user_data.get("referrals", [])
    bonus_level = user_data.get("bonus_level", 0)

    photo = types.InputFile("media/bonus.jpg")
    caption = (
        "🎁 <b>Do'stlaringizni taklif eting va pullik kanallarimizga bepul kiring!</b>\n\n"
        "👥 <b>20 do‘st</b> — \"Videodarslar 1-oy\"\n"
        "👥 <b>40 do‘st</b> — \"Videodarslar 2-oy\"\n"
        "👥 <b>60 do‘st</b> — \"Videodarslar 3-oy\"\n"
        "👥 <b>80 do‘st</b> — \"Videodarslar 4-oy\"\n\n"
        "📌 Har bir bosqich uchun maxsus kanal havolasi beriladi.\n"
        f"✅ Siz hozirda {len(referrals)} ta do‘st taklif qilgansiz."
    )

    await message.answer_photo(photo, caption=caption, parse_mode="HTML")

    if len(referrals) >= 80 and bonus_level < 4:
        await send_secret_channel(user_id, 4)
        user_data["bonus_level"] = 4
        save_data(data)
    elif len(referrals) >= 60 and bonus_level < 3:
        await send_secret_channel(user_id, 3)
        user_data["bonus_level"] = 3
        save_data(data)
    elif len(referrals) >= 40 and bonus_level < 2:
        await send_secret_channel(user_id, 2)
        user_data["bonus_level"] = 2
        save_data(data)
    elif len(referrals) >= 20 and bonus_level < 1:
        await send_secret_channel(user_id, 1)
        user_data["bonus_level"] = 1
        save_data(data)


@dp.message_handler(commands=["start"])
@dp.message_handler(lambda msg: msg.text == "🚀 Start ✅")
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.full_name
    data = load_data()

    if str(user_id) not in data:
        data[str(user_id)] = {
            "referrals": [],
            "joined": False,
            "bonus_level": 0,
            "temp_ref_id": None
        }

    args = message.get_args()
    if args and args != str(user_id):
        data[str(user_id)]["temp_ref_id"] = str(args)

    not_joined = await get_not_subscribed_channels(bot, user_id)

    if not_joined:
        data[str(user_id)]["joined"] = False
        save_data(data)

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🚀 Start ✅")

        text = "❗ Quyidagi kanallarga obuna bo‘ling:\n\n"
        inline = types.InlineKeyboardMarkup()
        
        for ch in not_joined:
            username_clean = ch["username"].lstrip("@")
            title = ch["title"]
            text += f"🔸 <a href='https://t.me/{username_clean}'>{title}</a>\n"
            inline.add(types.InlineKeyboardButton(
                text=f"📲 {title}",
                url=f"https://t.me/{username_clean}"
            ))

        await message.answer(text, reply_markup=inline, parse_mode="HTML", disable_web_page_preview=True)
        await message.answer("Obuna bo‘lgach, «🚀 Start ✅» tugmasini bosing 👇", reply_markup=markup)
        return

    data[str(user_id)]["joined"] = True

    temp_ref_id = data[str(user_id)].get("temp_ref_id")
    if temp_ref_id and temp_ref_id != str(user_id) and temp_ref_id in data:
        ref_user = data[temp_ref_id]
        if str(user_id) not in ref_user["referrals"]:
            ref_user["referrals"].append(str(user_id))
            referral_count = len(ref_user["referrals"])
            old_level = ref_user.get("bonus_level", 0)
            new_level = min(4, referral_count // 20)
            
            if new_level > old_level:
                ref_user["bonus_level"] = new_level
                await send_secret_channel(int(temp_ref_id), new_level)

        data[str(user_id)]["temp_ref_id"] = None

    save_data(data)

    try:
        reklama_text = load_reklama_text()
        if os.path.exists(REKLAMA_FILE):
            with open(REKLAMA_FILE, "rb") as video_file:
                await bot.send_video(
                    chat_id=message.chat.id,
                    video=video_file,
                    caption=reklama_text,
                    parse_mode="Markdown"
                )
        else:
            await message.answer(reklama_text)
    except Exception as e:
        logging.error(f"Video yuborishda xatolik: {e}")
        await message.answer("🎬 Reklama videosi")

    ref_count = len(data[str(user_id)]["referrals"])
    btns = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btns.add("🔗 Ishtirok etish", "📊 Reyting", "🎁 Sovrinlar")
    btns.add("🔐 Bonus kanallar")
    if str(user_id) in ADMIN_IDS:
        btns.add("📢 Xabar yuborish", "🎬 Reklamani o‘zgartirish")

    await message.answer(welcome_text(username, ref_count), reply_markup=btns)

@dp.message_handler(lambda msg: msg.text == "🚀 Start")
async def recheck_subs(message: types.Message):
    user_id = message.from_user.id
    not_joined = await get_not_subscribed_channels(bot, user_id)

    if not_joined:
        text = "🚫 Hali ham quyidagi kanallarga obuna emassiz:\n\n"
        inline = types.InlineKeyboardMarkup()
        for ch in not_joined:
            username_clean = ch["username"].lstrip("@")
            title = ch["title"]
            text += f"🔸 <a href='https://t.me/{username_clean}'>{title}</a>\n"
            inline.add(types.InlineKeyboardButton(
                text=f"📲 {title}",
                url=f"https://t.me/{username_clean}"
            ))
        text += "\n\nIltimos, barcha kanallarga obuna bo‘ling va qaytadan «✅ Start» tugmasini bosing."
        await message.answer(text, reply_markup=inline, parse_mode="HTML", disable_web_page_preview=True)
        return

    data = load_data()
    if str(user_id) in data:
        data[str(user_id)]["joined"] = True
        
        temp_ref_id = data[str(user_id)].get("temp_ref_id")
        if temp_ref_id and temp_ref_id != str(user_id) and temp_ref_id in data:
            ref_user = data[temp_ref_id]
            if str(user_id) not in ref_user["referrals"]:
                ref_user["referrals"].append(str(user_id))
                referral_count = len(ref_user["referrals"])
                old_level = ref_user.get("bonus_level", 0)
                new_level = min(4, referral_count // 20)
                
                if new_level > old_level:
                    ref_user["bonus_level"] = new_level
                    await send_secret_channel(int(temp_ref_id), new_level)
        
        data[str(user_id)]["temp_ref_id"] = None
        save_data(data)

    await start_handler(message)

dp.callback_query_handler(lambda c: c.data == "check_subs")
async def check_subscriptions(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.full_name
    data = load_data()

    # Tuzatish: bot argumentini qo'shish
    if not await check_subs(bot, user_id):
        return await callback.message.answer("❗ Iltimos, barcha kanallarga obuna bo‘ling!")

    data[str(user_id)]["joined"] = True

    temp_ref = data[str(user_id)].get("temp_ref_id")
    if temp_ref and temp_ref != str(user_id):
        ref_id = temp_ref
        if ref_id in data and str(user_id) not in data[ref_id]["referrals"]:
            data[ref_id]["referrals"].append(str(user_id))
            referral_count = len(set(data[ref_id]["referrals"]))
            old_level = data[ref_id].get("bonus_level", 0)
            new_level = min(4, referral_count // 20)  # Max 4 level
            if new_level > old_level:
                data[ref_id]["bonus_level"] = new_level
                await send_secret_channel(int(ref_id), new_level)

    save_data(data)
    ref_count = len(data[str(user_id)]["referrals"])

    try:
        await callback.message.delete()
    except Exception:
        pass

    await bot.send_message(
        user_id,
        welcome_text(username, ref_count),
        reply_markup=types.ReplyKeyboardMarkup(
            resize_keyboard=True, 
            row_width=2
        ).add(
            "🔗 Ishtirok etish", 
            "📊 Reyting", 
            "🎁 Sovrinlar",
            "🔐 Bonus kanallar"
        )
    )
    await callback.answer("✅ Obuna tasdiqlandi")

    try:
        reklama_text = load_reklama_text()
        if os.path.exists(REKLAMA_FILE):
            with open(REKLAMA_FILE, "rb") as video_file:
                await bot.send_video(
                    chat_id=user_id,
                    video=video_file,
                    caption=reklama_text,
                    parse_mode="Markdown"
                )
        else:
            await bot.send_message(user_id, reklama_text)
    except Exception as e:
        logging.error(f"Video send error: {e}")
        await bot.send_message(user_id, "🎬 Reklama videosi")

@dp.message_handler(lambda m: m.text == "🔗 Ishtirok etish")
@require_subscription(bot)
async def send_referral_link(message: types.Message):
    user_id = message.from_user.id
    link = referral_link(user_id)
    photo_path = "media/referal.jpg"

    caption = (
        "<b>Siz ham ona tili va adabiyot fanidan milliy sertifikat bo'yicha bir haftalik marafonda ishtirok eting</b>\n"
        "Shartlarni bajaring va qimmatli mukofotlarga ega bo'ling! 🎬 2-5-avgust kunlari katta marafon bo’ladi\n\n"

        "📨 Ushbu xabarni do'stingizga yuboring va u hamkor kanallarga obuna bo‘lsa, sizga 1 ball qo‘shiladi.\n"
        "🎯 Har 20 ta do‘stingiz qo‘shilganda sizga maxfiy pullik darslar havolasi beriladi va ballaringiz ortib boradi.\n\n"

        "<b>📆 2-avgustga qadar do‘stlaringizni taklif qiling!</b>\n"
        "🏆 Eng ko‘p ball to‘plagan 3 ishtirokchiga quyidagi mukofotlar beriladi:\n"
        "🥇 1-o‘rin — Planshet\n"
        "🥈 2-o‘rin — Elektron kitob qurilmasi\n"
        "🥉 3-o‘rin — 400.000 so‘m pul\n\n"
        "🎁 Qolgan 20 ishtirokchiga 50.000 so‘mdan pul mukofoti beriladi!\n\n"
        f"<b>📢 Sizning referal havolangiz:</b>\n{link}"
    )

    await message.answer_photo(
        types.InputFile(photo_path),
        caption=caption,
        parse_mode="HTML"
    )


@dp.message_handler(lambda m: m.text == "🎁 Sovrinlar")
@require_subscription(bot)
async def rewards_handler(message: types.Message):
    user_id = message.from_user.id
    data = load_data()
    user_data = data.get(str(user_id), {})

    if not user_data.get("joined", False):
        await message.answer("❌ Sovrinlar bo‘limiga kirish uchun barcha kanallarga obuna bo‘ling!")
        return

    ref_count = len(user_data.get("referrals", []))

    # 📸 Rasm yuborish
    photo_path = "media/referal.jpg"
    await message.answer_photo(
        types.InputFile(photo_path),
        caption="🏆 <b>Referal reyting asosida sovrinlar quyidagicha taqsimlanadi:</b>",
        parse_mode="HTML"
    )

    # 🎯 TOP 10 reyting
    top_users = sorted(
        [(uid, len(info.get("referrals", []))) for uid, info in data.items() if info.get("joined")],
        key=lambda x: x[1],
        reverse=True
    )[:10]

    top_text = "<b>🏅 TOP 10 ishtirokchi:</b>\n"
    for i, (uid, count) in enumerate(top_users, start=1):
        try:
            user = await bot.get_chat(uid)
            full_name = user.full_name
            username = f"@{user.username}" if user.username else "—"
            mention = f"<a href='tg://user?id={uid}'>{full_name}</a>"
        except Exception:
            mention = f"ID: <code>{uid}</code>"
            username = "—"

        top_text += f"{i}. {mention} ({username}) — <b>{count}</b> ta do‘st\n"

    # 📄 Sovrinlar matni
    description = (
        "🎁 <b>Mavjud sovrinlar:</b>\n\n"
        "🥇 1-o'rin — Planshet\n"
        "🥈 2-o'rin — Kitob o'qiydigan qurilma\n"
        "🥉 3-o'rin — 400.000 so'm pul\n"
        "🏅 Qolgan 20 ta o'rin — 50.000 so'm pul mukofoti\n\n"
        "🎁 <b>Har 20 do‘st uchun maxsus pullik ma’lumotlar taqdim etiladi.</b>\n\n"
        "Qancha ko'p do'st taklif qilsangiz, shuncha ko'p ball to‘playsiz va mukofotga yaqinlashasiz.\n"
        "Hoziroq \"➕ Ishtirok etish\" tugmasini bosing va sizga berilgan havolani do‘stlaringizga yuboring.\n\n"
        f"👥 Siz hozircha <b>#{ref_count}</b> ta do‘st taklif qilgansiz.\n"
    )

    await message.answer(description + "\n" + top_text, parse_mode="HTML")

@dp.message_handler(lambda m: m.text == "📊 Reyting")
@require_subscription(bot)
async def show_rating(message: types.Message):
    data = load_data()
    users = [(uid, info) for uid, info in data.items() if info.get("joined")]
    users.sort(key=lambda x: len(x[1]["referrals"]), reverse=True)

    # Reyting xabari matni
    text = (
        "<b>🏆 Reyting va Mukofotlar:</b>\n\n"
        "Reytingning 3 ta o'riniga quyidagi mukofotlar beriladi:\n"
        "🥇 1-o'rin — Planshet\n"
        "🥈 2-o'rin — Kitob o'qiydigan qurilma\n"
        "🥉 3-o'rin — 400.000 so'm pul\n\n"
        "🎁 Keyingi 20 ta o‘ringa — 50.000 so‘mdan pul mukofoti\n\n"
        "🎯 Har 20 ball uchun sizga maxfiy bonus kanal havolasi yuboriladi\n\n"
        "👥 <b>Eng ko‘p odam qo‘shgan ishtirokchilar ro‘yxati:</b>\n"
    )

    for i, (uid, info) in enumerate(users[:10], 1):
        try:
            user = await bot.get_chat(int(uid))
            name = user.full_name
            username = f"@{user.username}" if user.username else "Foydalanuvchi"
            count = len(info["referrals"])
            text += f"{i}. {name} ({username}) — {count} ta\n"
        except:
            text += f"{i}. [Noma'lum foydalanuvchi] — {len(info['referrals'])} ta\n"

    # Agar foydalanuvchi reytingda pastda bo‘lsa ham o‘rni ko‘rsatiladi
    current_uid = str(message.from_user.id)
    if current_uid in data:
        user_data = data[current_uid]
        if user_data.get("joined"):
            user_pos = next((i for i, (uid, _) in enumerate(users, 1) if uid == current_uid), None)
            if user_pos and user_pos > 10:
                count = len(user_data["referrals"])
                text += f"\n📌 Sizning o‘rningiz: {user_pos} — {count} ta"

    # Rasm bilan birga yuborish
    photo_path = "media/reyting.jpg"
    await message.answer_photo(
        types.InputFile(photo_path),
        caption=text,
        parse_mode="HTML"
    )


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