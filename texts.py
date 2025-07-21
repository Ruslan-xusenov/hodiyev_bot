def welcome_text(username, refer_count):
    return f"""👋 Salom, {username}!

Ushbu bot orqali yopiq kanallarga kirish imkoniyatiga ega bo‘lasiz. Har bir kanal uchun 20 ta do‘stingizni taklif qilishingiz kerak.

📨 Siz {refer_count} do‘stingizni taklif qilgansiz.
"""

def referral_link(user_id):
    return f"https://t.me/hodiyev_konkursbot?start={user_id}"

def subscription_text():
    return "👇 Davom etish uchun quyidagi kanallarga obuna bo‘ling va qaytadan /start bosing:"

def admin_menu_text():
    return "🛠 <b>Admin paneli</b>\nQuyidagi funksiyalardan birini tanlang:"