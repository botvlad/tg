import telebot
from telebot import types
import sqlite3
import time
import os
from flask import Flask
from threading import Thread

# --- НАСТРОЙКИ ДЛЯ RENDER (ЧТОБЫ БОТ НЕ СПАЛ) ---
app = Flask('')

@app.route('/')
def home():
    return "Бот запущен и работает 24/7!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- ОСНОВНОЙ КОД БОТА ---
TOKEN = "8310349633:AAGtW1gAeSmdohMVaCOEcz73Ef7tIkbUNSQ"
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
    db_query('''CREATE TABLE IF NOT EXISTS promo_codes (code TEXT PRIMARY KEY, reward REAL, uses_left INTEGER)''')
    db_query('''CREATE TABLE IF NOT EXISTS used_promos (user_id INTEGER, code TEXT, PRIMARY KEY(user_id, code))''')

# --- КЛАВИАТУРЫ ---
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🎁 Бонус", callback_data="bonus"),
        types.InlineKeyboardButton("👥 Рефералы", callback_data="refs"),
        types.InlineKeyboardButton("🎫 Промокод", callback_data="promo"),
        types.InlineKeyboardButton("💳 Вывод", callback_data="withdraw_menu"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="stats"),
        types.InlineKeyboardButton("📢 Каналы", callback_data="channels")
    )
    return markup

def get_withdraw_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("50 ⭐️", callback_data="wd_50"),
        types.InlineKeyboardButton("100 ⭐️", callback_data="wd_100"),
        types.InlineKeyboardButton("200 ⭐️", callback_data="wd_200"),
        types.InlineKeyboardButton("500 ⭐️", callback_data="wd_500"),
        types.InlineKeyboardButton("1000 ⭐️", callback_data="wd_1000"),
        types.InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")
    )
    return markup

# --- ОБРАБОТЧИКИ ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    username = message.from_user.username or "User"
    
    # Реферальная система
    args = message.text.split()
    referrer_id = 0
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])

    user = db_query("SELECT * FROM users WHERE user_id = ?", (uid,))
    if not user:
        db_query("INSERT INTO users (user_id, username, referrer_id) VALUES (?, ?, ?)", (uid, username, referrer_id))
        if referrer_id != 0:
            db_query("UPDATE users SET referrals = referrals + 1, balance = balance + 1 WHERE user_id = ?", (referrer_id,))
            try:
                bot.send_message(referrer_id, f"🎉 У вас новый реферал! +1 ⭐️")
            except: pass
    
    bot.send_message(uid, f"🌟 <b>Добро пожаловать, {username}!</b>\n\nЗдесь ты можешь заработать звезды!", 
                     reply_markup=get_main_keyboard(), parse_mode="HTML")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id in ADMIN_IDS:
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("➕ Добавить канал", callback_data="adm_add_chan"))
        m.add(types.InlineKeyboardButton("🎁 Создать промо", callback_data="adm_add_promo"))
        m.add(types.InlineKeyboardButton("📢 Рассылка", callback_data="adm_blast"))
        bot.send_message(message.chat.id, "🛠 <b>Админ-панель:</b>", reply_markup=m, parse_mode="HTML")

# --- ЛОГИКА CALLBACK ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = call.from_user.id
    user_data = db_query("SELECT balance, last_bonus FROM users WHERE user_id = ?", (uid,))
    if not user_data: return
    balance, last_bonus = user_data[0]

    if call.data == "main_menu":
        bot.edit_message_text(f"🌟 <b>Главное меню</b>\n💰 Баланс: <b>{balance} ⭐️</b>", 
                             call.message.chat.id, call.message.message_id, 
                             reply_markup=get_main_keyboard(), parse_mode="HTML")

    elif call.data == "bonus":
        now = int(time.time())
        if now - last_bonus >= 86400: # 24 часа
            reward = 1.5
            db_query("UPDATE users SET balance = balance + ?, last_bonus = ? WHERE user_id = ?", (reward, now, uid))
            bot.answer_callback_query(call.id, f"✅ Вы получили {reward} ⭐️", show_alert=True)
        else:
            wait = (86400 - (now - last_bonus)) // 3600
            bot.answer_callback_query(call.id, f"❌ Бонус доступен через {wait} ч.", show_alert=True)

    elif call.data == "stats":
        total = db_query("SELECT COUNT(*) FROM users")[0][0]
        bot.edit_message_text(f"📊 <b>Статистика бота:</b>\n👥 Всего пользователей: {total}\n💰 Твой баланс: {balance} ⭐️", 
                             call.message.chat.id, call.message.message_id, 
                             reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")), parse_mode="HTML")

    elif call.data == "promo":
        msg = bot.send_message(call.message.chat.id, "🎁 <b>Введите промокод:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_promo)

    elif call.data == "withdraw_menu":
        bot.edit_message_text("💳 <b>Выберите сумму для вывода:</b>", call.message.chat.id, call.message.message_id, reply_markup=get_withdraw_keyboard(), parse_mode="HTML")

    elif call.data.startswith("wd_"):
        amount = int(call.data.split("_")[1])
        if balance >= amount:
            pay_text = f"🌟 <b>Новая заявка!</b>\n👤 ID <code>{uid}</code>\n💰 Сумма: <b>{amount} ⭐️</b>\n🔄 Статус: Ожидает обработки ⚙️"
            m = types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("✅ Одобрить", callback_data=f"adm_ok_{uid}_{amount}"), 
                types.InlineKeyboardButton("❌ Отклонить", callback_data=f"adm_no_{uid}")
            )
            bot.send_message(PAYMENT_CHANNEL_ID, pay_text, reply_markup=m, parse_mode="HTML")
            db_query("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, uid))
            bot.answer_callback_query(call.id, "✅ Заявка отправлена!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ Недостаточно средств", show_alert=True)

# --- ФУНКЦИИ ПРОМОКОДОВ ---
def process_promo(message):
    uid = message.from_user.id
    code_text = message.text
    promo = db_query("SELECT reward, uses_left FROM promo_codes WHERE code = ?", (code_text,))
    
    if not promo:
        bot.send_message(uid, "❌ Такого промокода нет.")
        return
    
    used = db_query("SELECT * FROM used_promos WHERE user_id = ? AND code = ?", (uid, code_text))
    if used:
        bot.send_message(uid, "❌ Вы уже использовали этот код.")
        return

    reward, left = promo[0]
    if left > 0:
        db_query("UPDATE promo_codes SET uses_left = uses_left - 1 WHERE code = ?", (code_text,))
        db_query("INSERT INTO used_promos (user_id, code) VALUES (?, ?)", (uid, code_text))
        db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, uid))
        bot.send_message(uid, f"✅ Промокод активирован! +{reward} ⭐️")
    else:
        bot.send_message(uid, "❌ Промокод закончился.")

# --- ЗАПУСК ---
if __name__ == "__main__":
    init_db()
    keep_alive() # Этот поток нужен для Render
    print("Бот успешно запущен!")
    bot.polling(none_stop=True)
    
