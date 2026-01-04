import telebot
from telebot import types
import sqlite3
import time
import os
from flask import Flask
from threading import Thread

# --- НАСТРОЙКИ ---
TOKEN = "8575208075:AAGPuQWeTjo8DbQQgKrJdK4ww86RDvp5vuA"
bot = telebot.TeleBot(TOKEN)

# Админы и Канал выплат
ADMIN_IDS = [8063642030, 8453400444] 
PAYMENT_CHANNEL_ID = "@bobroplata"  # Твой новый канал для выплат

# --- СЕРВЕР ДЛЯ RENDER ---
app = Flask('')
@app.route('/')
def home(): return "EliteStars System Active"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- БАЗА ДАННЫХ ---
DB_PATH = 'bot_database.db'

def db_query(sql, params=()):
    with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
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
    if not db_query("SELECT * FROM sponsors"):
        db_query("INSERT INTO sponsors (channel_id, link) VALUES (?, ?)", ("@EliteStarsH", "https://t.me/EliteStarsH"))

# --- ПРОВЕРКА ПОДПИСКИ ---
def check_sub(user_id):
    sponsors = db_query("SELECT channel_id FROM sponsors")
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
        types.InlineKeyboardButton("🌟 Заработать", callback_data="earn"),
        types.InlineKeyboardButton("📩 Вывод", callback_data="withdraw_menu"),
        types.InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        types.InlineKeyboardButton("🎁 Бонус", callback_data="bonus")
    )
    return markup

# --- КОМАНДЫ АДМИНА ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id in ADMIN_IDS:
        bot.send_message(message.chat.id, "🛠 <b>Админ-панель</b>\n\n`/give ID СУММА` — Выдать\n`/take ID СУММА` — Забрать", parse_mode="HTML")

@bot.message_handler(commands=['give'])
def give_stars(message):
    if message.from_user.id in ADMIN_IDS:
        try:
            _, tid, amt = message.text.split()
            db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (float(amt), int(tid)))
            bot.send_message(message.chat.id, f"✅ Выдано {amt} ⭐️ пользователю {tid}")
            try: bot.send_message(int(tid), f"🎁 Начислено {amt} ⭐️!")
            except: pass
        except: bot.send_message(message.chat.id, "Ошибка! Формат: `/give ID СУММА`")

# --- СТАРТ ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    uname = message.from_user.username or "User"
    user = db_query("SELECT user_id FROM users WHERE user_id = ?", (uid,))
    if not user:
        ref_id = 0
        args = message.text.split()
        if len(args) > 1 and args[1].isdigit(): ref_id = int(args[1])
        db_query("INSERT INTO users (user_id, username, referrer_id) VALUES (?, ?, ?)", (uid, uname, ref_id))
    
    if check_sub(uid):
        u_data = db_query("SELECT is_activated, referrer_id FROM users WHERE user_id = ?", (uid,))
        if u_data and u_data[0][0] == 0:
            rid = u_data[0][1]
            db_query("UPDATE users SET is_activated = 1 WHERE user_id = ?", (uid,))
            if rid and rid != 0:
                db_query("UPDATE users SET balance = balance + 5, referrals = referrals + 1 WHERE user_id = ?", (rid,))
                try: bot.send_message(rid, f"🎉 +5 ⭐️ за друга @{uname}!")
                except: pass
        bot.send_message(message.chat.id, "✨ <b>Меню:</b>", reply_markup=get_main_menu(), parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "⚠️ Подпишитесь на @EliteStarsH и нажмите /start")

# --- ОБРАБОТКА КНОПОК ---
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    uid = call.from_user.id
    
    # Кнопки админа в канале @bobroplata
    if call.data.startswith("adm_"):
        if uid not in ADMIN_IDS: return
        action = call.data.split("_")[1]
        try:
            target_uid = int(call.message.text.split("ID: ")[1].split("\n")[0])
            if action == "ok":
                bot.edit_message_text(call.message.text + "\n\n✅ <b>ВЫПЛАЧЕНО</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML")
                bot.send_message(target_uid, "✅ Ваша заявка одобрена, звёзды отправлены!")
            else:
                bot.edit_message_text(call.message.text + "\n\n❌ <b>ОТКЛОНЕНО</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML")
                bot.send_message(target_uid, "❌ Ваша заявка на вывод отклонена.")
        except: pass
        return

    # Меню пользователя
    if call.data == "profile":
        res = db_query("SELECT balance, referrals FROM users WHERE user_id = ?", (uid,))
        bot.edit_message_text(f"👤 <b>Профиль:</b>\n🆔 ID: <code>{uid}</code>\n💰 Баланс: <b>{res[0][0]:.2f} ⭐️</b>", call.message.chat.id, call.message.message_id, reply_markup=get_main_menu(), parse_mode="HTML")

    elif call.data == "withdraw_menu":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("15 ⭐️", callback_data="wd_15"), types.InlineKeyboardButton("25 ⭐️", callback_data="wd_25"))
        m.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="main_menu"))
        bot.edit_message_text("💳 Выберите сумму:", call.message.chat.id, call.message.message_id, reply_markup=m)

    elif call.data.startswith("wd_"):
        amt = int(call.data.split("_")[1])
        bal = db_query("SELECT balance FROM users WHERE user_id = ?", (uid,))[0][0]
        if bal >= amt:
            db_query("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amt, uid))
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ Одобрить", callback_data="adm_ok"), types.InlineKeyboardButton("❌ Отклонить", callback_data="adm_no"))
            bot.send_message(PAYMENT_CHANNEL_ID, f"🌟 <b>ЗАЯВКА НА ВЫВОД</b>\n🆔 ID: {uid}\n💰 Сумма: {amt} ⭐️", reply_markup=markup, parse_mode="HTML")
            bot.answer_callback_query(call.id, "✅ Заявка отправлена в @bobroplata!", show_alert=True)
        else: bot.answer_callback_query(call.id, "❌ Недостаточно звёзд!", show_alert=True)

    elif call.data == "main_menu":
        bot.edit_message_text("✨ Меню:", call.message.chat.id, call.message.message_id, reply_markup=get_main_menu())

if __name__ == '__main__':
    init_db()
    Thread(target=run_web).start()
    bot.infinity_polling()
