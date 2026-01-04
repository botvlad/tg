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

# Список ID админов (ОБЯЗАТЕЛЬНО проверь свои ID тут)
ADMIN_IDS = [8063642030, 8453400444] 

# ID канала для заявок на вывод
PAYMENT_CHANNEL_ID = "@EliteStarsD" 

# --- СЕРВЕР ДЛЯ RENDER ---
app = Flask('')
@app.route('/')
def home(): return "EliteStars System is Live!"

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
    check = db_query("SELECT count(*) FROM sponsors")
    if check[0][0] == 0:
        db_query("INSERT INTO sponsors (channel_id, link) VALUES (?, ?)", ("@EliteStarsH", "https://t.me/EliteStarsH"))

# --- АДМИН-КОМАНДЫ (ТОЛЬКО ДЛЯ ADMIN_IDS) ---

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id not in ADMIN_IDS:
        return # Обычные пользователи ничего не увидят
    
    sponsors = db_query("SELECT channel_id FROM sponsors")
    sp_text = "\n".join([f"🔹 {s[0]}" for s in sponsors])
    text = (f"🛠 <b>АДМИН-ПАНЕЛЬ</b>\n\n"
            f"📡 <b>Спонсоры:</b>\n{sp_text}\n\n"
            f"💰 <b>Команды баланса:</b>\n"
            f"➕ <code>/give ID СУММА</code> — Выдать\n"
            f"➖ <code>/take ID СУММА</code> — Забрать\n\n"
            f"📊 <code>/stats</code> — Кол-во юзеров")
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(commands=['give'])
def give_stars(message):
    if message.from_user.id in ADMIN_IDS:
        try:
            parts = message.text.split()
            target_id = int(parts[1])
            amount = float(parts[2])
            
            # Проверяем есть ли юзер в базе
            user = db_query("SELECT user_id FROM users WHERE user_id = ?", (target_id,))
            if not user:
                bot.send_message(message.chat.id, f"❌ Ошибка: Юзер <code>{target_id}</code> еще не заходил в бота!", parse_mode="HTML")
                return

            db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, target_id))
            bot.send_message(message.chat.id, f"✅ Выдано <b>{amount}</b> ⭐️ пользователю <code>{target_id}</code>", parse_mode="HTML")
            try: bot.send_message(target_id, f"🎁 Админ начислил вам <b>{amount}</b> ⭐️!")
            except: pass
        except:
            bot.send_message(message.chat.id, "⚠️ Формат: `/give ID СУММА`")

@bot.message_handler(commands=['take'])
def take_stars(message):
    if message.from_user.id in ADMIN_IDS:
        try:
            parts = message.text.split()
            target_id, amount = int(parts[1]), float(parts[2])
            db_query("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, target_id))
            bot.send_message(message.chat.id, f"✅ Списано <b>{amount}</b> ⭐️ у <code>{target_id}</code>", parse_mode="HTML")
        except:
            bot.send_message(message.chat.id, "⚠️ Формат: `/take ID СУММА`")

@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id in ADMIN_IDS:
        count = db_query("SELECT count(*) FROM users")[0][0]
        bot.send_message(message.chat.id, f"📊 В базе данных: {count} пользователей")

# --- ГЛАВНАЯ ЛОГИКА (START И МЕНЮ) ---

def check_sub(user_id):
    sponsors = db_query("SELECT channel_id FROM sponsors")
    for s in sponsors:
        try:
            status = bot.get_chat_member(s[0], user_id).status
            if status not in ['member', 'administrator', 'creator']: return False
        except: continue
    return True

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    uname = message.from_user.username or "User"
    
    # Регистрация юзера если его нет
    user = db_query("SELECT user_id FROM users WHERE user_id = ?", (uid,))
    if not user:
        ref_id = 0
        args = message.text.split()
        if len(args) > 1 and args[1].isdigit():
            ref_id = int(args[1])
        db_query("INSERT INTO users (user_id, username, referrer_id) VALUES (?, ?, ?)", (uid, uname, ref_id))
    
    if check_sub(uid):
        # Начисление за рефа при активации
        u_data = db_query("SELECT is_activated, referrer_id FROM users WHERE user_id = ?", (uid,))
        if u_data and u_data[0][0] == 0:
            rid = u_data[0][1]
            db_query("UPDATE users SET is_activated = 1 WHERE user_id = ?", (uid,))
            if rid and rid != 0:
                db_query("UPDATE users SET balance = balance + 5, referrals = referrals + 1 WHERE user_id = ?", (rid,))
                try: bot.send_message(rid, f"🎉 Друг @{uname} подписался! Вам +5 ⭐️")
                except: pass
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🌟 Заработать", callback_data="earn"),
            types.InlineKeyboardButton("📩 Вывод", callback_data="withdraw_menu"),
            types.InlineKeyboardButton("👤 Профиль", callback_data="profile"),
            types.InlineKeyboardButton("🎁 Бонус", callback_data="bonus")
        )
        bot.send_message(message.chat.id, "✨ <b>Меню EliteStars:</b>", reply_markup=markup, parse_mode="HTML")
    else:
        # Кнопки подписки
        sponsors = db_query("SELECT channel_id, link FROM sponsors")
        markup = types.InlineKeyboardMarkup()
        for i, s in enumerate(sponsors, 1):
            markup.add(types.InlineKeyboardButton(f"⭐️ Канал №{i}", url=s[1]))
        markup.add(types.InlineKeyboardButton("✅ Проверить подписку", callback_data="sub_check"))
        bot.send_message(message.chat.id, "⚠️ <b>Подпишитесь для работы:</b>", reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    uid = call.from_user.id
    
    if call.data == "sub_check":
        if check_sub(uid):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ Подписка не найдена!", show_alert=True)
    
    elif call.data == "profile":
        res = db_query("SELECT balance, referrals FROM users WHERE user_id = ?", (uid,))
        bot.edit_message_text(f"👤 <b>Профиль:</b>\n🆔 ID: <code>{uid}</code>\n💰 Баланс: <b>{res[0][0]:.2f} ⭐️</b>\n👥 Рефералы: {res[0][1]}", 
                              call.message.chat.id, call.message.message_id, parse_mode="HTML")

# --- ЗАПУСК ---
if __name__ == '__main__':
    init_db()
    Thread(target=run_web).start()
    bot.infinity_polling()
