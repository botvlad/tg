import telebot
from telebot import types
import sqlite3
import time
import os
from flask import Flask
from threading import Thread

# --- НАСТРОЙКИ RENDER (НЕ ТРОГАТЬ) ---
app = Flask('')
@app.route('/')
def home():
    return "Бот EliteStars активен!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- ОСНОВНЫЕ НАСТРОЙКИ БОТА ---
TOKEN = "8575208075:AAGPuQWeTjo8DbQQgKrJdK4ww86RDvp5vuA"
bot = telebot.TeleBot(TOKEN)

ADMIN_IDS = [8063642030, 8453400444] 
PAYMENT_CHANNEL_ID = "@EliteStarsD" 

# --- БАЗА ДАННЫХ ---
def db_query(sql, params=()):
    with sqlite3.connect('bot_database.db', check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        res = cursor.fetchall()
        conn.commit()
        return res

def init_db():
    db_query('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, 
        username TEXT, 
        balance REAL DEFAULT 0, 
        last_bonus INTEGER DEFAULT 0,
        referrals INTEGER DEFAULT 0,
        referrer_id INTEGER DEFAULT 0,
        is_activated INTEGER DEFAULT 0,
        is_banned INTEGER DEFAULT 0,
        last_seen INTEGER DEFAULT 0)''')
    db_query('''CREATE TABLE IF NOT EXISTS sponsors (channel_id TEXT PRIMARY KEY, link TEXT)''')
    db_query('''CREATE TABLE IF NOT EXISTS promocodes (code TEXT PRIMARY KEY, amount REAL, max_uses INTEGER, current_uses INTEGER DEFAULT 0)''')
    db_query('''CREATE TABLE IF NOT EXISTS used_promos (user_id INTEGER, code TEXT)''')
    
    check = db_query("SELECT count(*) FROM sponsors")
    if check[0][0] == 0:
        db_query("INSERT INTO sponsors (channel_id, link) VALUES (?, ?)", ("@EliteStarsH", "https://t.me/EliteStarsH"))

# --- ФУНКЦИИ ПРОВЕРКИ ---
def update_activity(uid):
    db_query("UPDATE users SET last_seen = ? WHERE user_id = ?", (int(time.time()), uid))

def get_sponsors():
    return db_query("SELECT channel_id, link FROM sponsors")

def check_sub(user_id):
    sponsors = get_sponsors()
    if not sponsors: return True
    for s in sponsors:
        try:
            status = bot.get_chat_member(s[0], user_id).status
            if status not in ['member', 'administrator', 'creator']: return False
        except: continue
    return True

# --- КЛАВИАТУРЫ ---
def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🌟 Заработать звёзды", callback_data="earn"),
        types.InlineKeyboardButton("📩 Вывести звёзды", callback_data="withdraw_menu"),
        types.InlineKeyboardButton("👤 Мой профиль", callback_data="profile"),
        types.InlineKeyboardButton("🎁 Бонус", callback_data="bonus"), 
        types.InlineKeyboardButton("🎁 Промокод", callback_data="promo"),          
        types.InlineKeyboardButton("🏆 ТОП 10", callback_data="top")
    )
    return markup

def get_withdraw_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("15 ⭐️", callback_data="wd_15"),
        types.InlineKeyboardButton("50 ⭐️", callback_data="wd_50"),
        types.InlineKeyboardButton("100 ⭐️", callback_data="wd_100"),
        types.InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")
    )
    return markup

# --- ЛОГИКА ПРОМОКОДОВ ---
def process_promo(message):
    uid = message.from_user.id
    code_text = message.text.strip().upper()
    update_activity(uid)
    promo = db_query("SELECT amount, max_uses, current_uses FROM promocodes WHERE code = ?", (code_text,))
    if not promo:
        bot.send_message(message.chat.id, "❌ Промокод не найден.", reply_markup=get_main_menu())
        return
    amount, max_uses, current_uses = promo[0]
    used = db_query("SELECT 1 FROM used_promos WHERE user_id = ? AND code = ?", (uid, code_text))
    if used:
        bot.send_message(message.chat.id, "⚠️ Вы уже активировали его.", reply_markup=get_main_menu())
        return
    if current_uses >= max_uses:
        bot.send_message(message.chat.id, "🚫 Лимит исчерпан.", reply_markup=get_main_menu())
        return
    db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, uid))
    db_query("UPDATE promocodes SET current_uses = current_uses + 1 WHERE code = ?", (code_text,))
    db_query("INSERT INTO used_promos (user_id, code) VALUES (?, ?)", (uid, code_text))
    bot.send_message(message.chat.id, f"✅ Начислено {amount} ⭐️", reply_markup=get_main_menu())

# --- ОБРАБОТЧИКИ ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    uname = message.from_user.username or "User"
    update_activity(uid)
    
    user = db_query("SELECT is_banned, is_activated, referrer_id FROM users WHERE user_id = ?", (uid,))
    if user and user[0][0] == 1:
        bot.send_message(uid, "🚫 Вы заблокированы.")
        return

    if not user:
        ref_id = 0
        args = message.text.split()
        if len(args) > 1 and args[1].isdigit(): ref_id = int(args[1])
        db_query("INSERT INTO users (user_id, username, referrer_id) VALUES (?, ?, ?)", (uid, uname, ref_id))

    if check_sub(uid):
        bot.send_message(uid, f"✨ <b>Привет, {uname}!</b>\nДобро пожаловать в EliteStars.", reply_markup=get_main_menu(), parse_mode="HTML")
    else:
        markup = types.InlineKeyboardMarkup()
        for i, s in enumerate(get_sponsors(), 1): markup.add(types.InlineKeyboardButton(f"⭐️ Канал {i}", url=s[1]))
        markup.add(types.InlineKeyboardButton("✅ Проверить", callback_data="sub_check"))
        bot.send_message(uid, "⚠️ <b>Подпишитесь на каналы:</b>", reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def cb_handler(call):
    uid = call.from_user.id
    update_activity(uid)
    
    if call.data == "sub_check":
        if check_sub(uid):
            bot.edit_message_text("✅ Доступ разрешен!", call.message.chat.id, call.message.message_id, reply_markup=get_main_menu())
        else: bot.answer_callback_query(call.id, "❌ Подпишитесь!", show_alert=True)
    
    res = db_query("SELECT balance, referrals, last_bonus FROM users WHERE user_id = ?", (uid,))
    if not res: return
    balance, refs, last_bonus = res[0]

    if call.data == "main_menu":
        bot.edit_message_text("✨ <b>Главное меню:</b>", call.message.chat.id, call.message.message_id, reply_markup=get_main_menu(), parse_mode="HTML")
    elif call.data == "profile":
        bot.edit_message_text(f"👤 <b>Профиль:</b>\n🆔 ID: <code>{uid}</code>\n💰 Баланс: {balance} ⭐️\n👥 Рефералы: {refs}", call.message.chat.id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")), parse_mode="HTML")
    elif call.data == "earn":
        bot.edit_message_text(f"🌟 <b>Твоя ссылка:</b>\n<code>https://t.me/{bot.get_me().username}?start={uid}</code>\n\n+5 ⭐️ за друга!", call.message.chat.id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")), parse_mode="HTML")
    elif call.data == "bonus":
        now = int(time.time())
        if now - last_bonus >= 86400:
            db_query("UPDATE users SET balance = balance + 1, last_bonus = ? WHERE user_id = ?", (now, uid))
            bot.answer_callback_query(call.id, "🎁 +1 ⭐️!", show_alert=True)
        else: bot.answer_callback_query(call.id, "⏰ Бонус раз в 24 часа!", show_alert=True)
    elif call.data == "promo":
        msg = bot.send_message(call.message.chat.id, "🎁 <b>Введите промокод:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_promo)
    elif call.data == "top":
        top = db_query("SELECT username, referrals FROM users ORDER BY referrals DESC LIMIT 10")
        text = "🏆 <b>ТОП 10 Рефоводов:</b>\n\n"
        for i, u in enumerate(top, 1): text += f"{i}. @{u[0]} — {u[1]} чел.\n"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")), parse_mode="HTML")
    elif call.data == "withdraw_menu":
        bot.edit_message_text("💳 <b>Выберите сумму:</b>", call.message.chat.id, call.message.message_id, reply_markup=get_withdraw_keyboard(), parse_mode="HTML")

# --- ЗАПУСК ---
if __name__ == "__main__":
    init_db()
    keep_alive() # Держит бота онлайн на Render
    print("Бот запущен!")
    bot.polling(none_stop=True)
