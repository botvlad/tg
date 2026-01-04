import telebot
from telebot import types
import sqlite3
import time

# --- НАСТРОЙКИ ---
TOKEN = "8310349633:AAGtW1gAeSmdohMVaCOEcz73Ef7tIkbUNSQ"
bot = telebot.TeleBot(TOKEN)

# Список ID админов
ADMIN_IDS = [8063642030, 8453400444] 

# ID канала для заявок
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
    # Таблица пользователей
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
    
    # Таблица спонсоров
    db_query('''CREATE TABLE IF NOT EXISTS sponsors (
        channel_id TEXT PRIMARY KEY, 
        link TEXT)''')

    # --- НОВЫЕ ТАБЛИЦЫ ДЛЯ ПРОМОКОДОВ ---
    db_query('''CREATE TABLE IF NOT EXISTS promocodes (
        code TEXT PRIMARY KEY, 
        amount REAL, 
        max_uses INTEGER, 
        current_uses INTEGER DEFAULT 0)''')
    
    db_query('''CREATE TABLE IF NOT EXISTS used_promos (
        user_id INTEGER, 
        code TEXT)''')
    
    # Инициализация спонсора по умолчанию
    check = db_query("SELECT count(*) FROM sponsors")
    if check[0][0] == 0:
        db_query("INSERT INTO sponsors (channel_id, link) VALUES (?, ?)", ("@EliteStarsH", "https://t.me/EliteStarsH"))

    # Миграции (на случай если колонки не создались)
    try: db_query("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")
    except: pass
    try: db_query("ALTER TABLE users ADD COLUMN last_seen INTEGER DEFAULT 0")
    except: pass

# --- ФУНКЦИИ ---
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
            if status not in ['member', 'administrator', 'creator']:
                return False
        except: continue
    return True

# --- КЛАВИАТУРЫ ---
def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🌟 Заработать звёзды", callback_data="earn"),
        types.InlineKeyboardButton("📩 Вывести звёзды", callback_data="withdraw_menu"),
        types.InlineKeyboardButton("👤 Мой профиль", callback_data="profile"),
        types.InlineKeyboardButton("🎁 Ежедневный бонус", callback_data="bonus"), 
        types.InlineKeyboardButton("🎁 Промокод", callback_data="promo"),         
        types.InlineKeyboardButton("🏆 Топ рефоводов", callback_data="top")
    )
    return markup

def get_withdraw_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("15 ⭐️", callback_data="wd_15"),
        types.InlineKeyboardButton("25 ⭐️", callback_data="wd_25"),
        types.InlineKeyboardButton("50 ⭐️", callback_data="wd_50"),
        types.InlineKeyboardButton("100 ⭐️", callback_data="wd_100"),
        types.InlineKeyboardButton("PREMIUM (350⭐️)", callback_data="wd_350"),
        types.InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")
    )
    return markup
# --- ЛОГИКА ПРОМОКОДОВ ---
def process_promo(message):
    uid = message.from_user.id
    code_text = message.text.strip().upper()
    update_activity(uid)
    
    # Ищем промокод в базе
    promo = db_query("SELECT amount, max_uses, current_uses FROM promocodes WHERE code = ?", (code_text,))
    
    if not promo:
        bot.send_message(message.chat.id, "❌ <b>Такого промокода не существует или он истек.</b>", reply_markup=get_main_menu(), parse_mode="HTML")
        return
    
    amount, max_uses, current_uses = promo[0]
    
    # Проверка, не юзал ли уже этот человек этот код
    already_used = db_query("SELECT 1 FROM used_promos WHERE user_id = ? AND code = ?", (uid, code_text))
    
    if already_used:
        bot.send_message(message.chat.id, "⚠️ <b>Вы уже активировали этот промокод ранее!</b>", reply_markup=get_main_menu(), parse_mode="HTML")
        return

    # Проверка лимита активаций
    if current_uses >= max_uses:
        bot.send_message(message.chat.id, "🚫 <b>К сожалению, лимит активаций этого кода исчерпан.</b>", reply_markup=get_main_menu(), parse_mode="HTML")
        return

    # Процесс активации
    db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, uid))
    db_query("UPDATE promocodes SET current_uses = current_uses + 1 WHERE code = ?", (code_text,))
    db_query("INSERT INTO used_promos (user_id, code) VALUES (?, ?)", (uid, code_text))
    
    bot.send_message(message.chat.id, f"✅ <b>Успешно! Начислено {amount} ⭐️</b>", reply_markup=get_main_menu(), parse_mode="HTML")

# --- АДМИН ПАНЕЛЬ ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id in ADMIN_IDS:
        update_activity(message.from_user.id)
        sponsors = get_sponsors()
        sp_text = "\n".join([f"🔹 {s[0]}" for s in sponsors])
        
        # Получаем список промокодов для админки
        promos = db_query("SELECT code, amount, current_uses, max_uses FROM promocodes")
        pr_text = "\n".join([f"🎫 <code>{p[0]}</code> | {p[1]}⭐️ | {p[2]}/{p[3]}" for p in promos])
        
        text = (f"🛠 <b>Админ-панель EliteStars</b>\n\n"
                f"👤 Вы: <code>{message.from_user.id}</code>\n\n"
                f"📡 <b>Спонсоры:</b>\n{sp_text if sp_text else 'Пусто'}\n"
                f"➕ <code>/add_sponsor @id link</code>\n"
                f"➖ <code>/del_sponsor @id</code>\n\n"
                f"🎫 <b>Промокоды:</b>\n{pr_text if pr_text else 'Нет активных'}\n"
                f"➕ <code>/add_promo КОД СУММА ЛИМИТ</code>\n"
                f"➖ <code>/del_promo КОД</code>\n\n"
                f"📊 <code>/stats</code> | 💰 <code>/give ID СУММА</code>\n"
                f"🚫 <code>/ban ID</code> | 🔓 <code>/unban ID</code>\n"
                f"📢 <code>/send ТЕКСТ</code> — Рассылка")
        bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(commands=['add_promo'])
def add_promo_cmd(message):
    if message.from_user.id in ADMIN_IDS:
        try:
            parts = message.text.split()
            code = parts[1].upper()
            amount = float(parts[2])
            limit = int(parts[3])
            db_query("INSERT OR REPLACE INTO promocodes (code, amount, max_uses) VALUES (?, ?, ?)", (code, amount, limit))
            bot.send_message(message.chat.id, f"✅ Промокод <b>{code}</b> на {amount}⭐️ (лимит {limit} чел.) создан!", parse_mode="HTML")
        except:
            bot.send_message(message.chat.id, "❌ Ошибка! Формат: <code>/add_promo GIFT100 100 50</code>", parse_mode="HTML")

@bot.message_handler(commands=['del_promo'])
def del_promo_cmd(message):
    if message.from_user.id in ADMIN_IDS:
        try:
            code = message.text.split()[1].upper()
            db_query("DELETE FROM promocodes WHERE code = ?", (code,))
            db_query("DELETE FROM used_promos WHERE code = ?", (code,))
            bot.send_message(message.chat.id, f"🗑 Промокод <b>{code}</b> полностью удален.", parse_mode="HTML")
        except:
            bot.send_message(message.chat.id, "❌ Формат: <code>/del_promo КОД</code>", parse_mode="HTML")
@bot.message_handler(commands=['stats'])
def get_stats(message):
    if message.from_user.id in ADMIN_IDS:
        now = int(time.time())
        limit = now - 900
        online_users = db_query("SELECT user_id, username FROM users WHERE last_seen > ?", (limit,))
        afk_users = db_query("SELECT user_id, username FROM users WHERE last_seen <= ?", (limit,))
        all_count = db_query("SELECT count(*) FROM users")[0][0]
        
        text = f"📊 <b>Статистика EliteStars</b>\n\n"
        text += f"🟢 <b>ОНЛАЙН: {len(online_users)}</b>\n"
        for u in online_users[:15]: text += f"└ <code>{u[0]}</code> | @{u[1]}\n"
        text += f"\n🔴 <b>АФК: {len(afk_users)}</b>\n"
        text += f"\n👥 <b>ВСЕГО: {all_count}</b>"
        bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(commands=['add_sponsor'])
def add_sponsor(message):
    if message.from_user.id in ADMIN_IDS:
        try:
            parts = message.text.split()
            channel_id, link = parts[1], parts[2]
            db_query("INSERT OR REPLACE INTO sponsors (channel_id, link) VALUES (?, ?)", (channel_id, link))
            bot.send_message(message.chat.id, f"✅ Спонсор {channel_id} добавлен!")
        except: bot.send_message(message.chat.id, "Формат: <code>/add_sponsor @канал ссылка</code>", parse_mode="HTML")

@bot.message_handler(commands=['del_sponsor'])
def del_sponsor(message):
    if message.from_user.id in ADMIN_IDS:
        try:
            channel_id = message.text.split()[1]
            db_query("DELETE FROM sponsors WHERE channel_id = ?", (channel_id,))
            bot.send_message(message.chat.id, f"🗑 Спонсор {channel_id} удален.")
        except: bot.send_message(message.chat.id, "Формат: <code>/del_sponsor @канал</code>", parse_mode="HTML")

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.from_user.id in ADMIN_IDS:
        try:
            tid = int(message.text.split()[1])
            db_query("UPDATE users SET is_banned = 1 WHERE user_id = ?", (tid,))
            bot.send_message(message.chat.id, f"🚫 Забанен: <code>{tid}</code>", parse_mode="HTML")
        except: pass

@bot.message_handler(commands=['unban'])
def unban_user(message):
    if message.from_user.id in ADMIN_IDS:
        try:
            tid = int(message.text.split()[1])
            db_query("UPDATE users SET is_banned = 0 WHERE user_id = ?", (tid,))
            bot.send_message(message.chat.id, f"🔓 Разбанен: <code>{tid}</code>", parse_mode="HTML")
        except: pass

@bot.message_handler(commands=['give'])
def give_stars(message):
    if message.from_user.id in ADMIN_IDS:
        try:
            parts = message.text.split()
            tid, amount = int(parts[1]), float(parts[2])
            db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, tid))
            bot.send_message(message.chat.id, f"✅ Выдано {amount}⭐️ пользователю <code>{tid}</code>", parse_mode="HTML")
        except: pass

@bot.message_handler(commands=['send'])
def broadcast(message):
    if message.from_user.id in ADMIN_IDS:
        text = message.text.replace("/send", "").strip()
        if not text: return
        users = db_query("SELECT user_id FROM users")
        for u in users:
            try: bot.send_message(u[0], text)
            except: continue
        bot.send_message(message.chat.id, "📢 Рассылка окончена.")

# --- ОБРАБОТЧИКИ ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    uname = message.from_user.username if message.from_user.username else "User"
    update_activity(uid)
    user = db_query("SELECT is_activated, referrer_id, is_banned FROM users WHERE user_id = ?", (uid,))
    
    if user and user[0][2] == 1:
        bot.send_message(message.chat.id, "🚫 Доступ заблокирован.")
        return
if not user:
        ref_id = 0
        args = message.text.split()
        if len(args) > 1:
            try:
                ref_id = int(args[1])
                if ref_id == uid: ref_id = 0
            except: pass
        db_query("INSERT INTO users (user_id, username, referrer_id, is_activated, is_banned, last_seen) VALUES (?, ?, ?, 0, 0, ?)", (uid, uname, ref_id, int(time.time())))
    
    if check_sub(uid):
        user_now = db_query("SELECT is_activated, referrer_id FROM users WHERE user_id = ?", (uid,))
        if user_now and user_now[0][0] == 0:
            rid = user_now[0][1]
            db_query("UPDATE users SET is_activated = 1 WHERE user_id = ?", (uid,))
            if rid != 0:
                db_query("UPDATE users SET balance = balance + 5, referrals = referrals + 1 WHERE user_id = ?", (rid,))
                try: bot.send_message(rid, f"🎉 Новый реферал @{uname} подписался! Вам +5 ⭐️")
                except: pass
        bot.send_message(message.chat.id, "✨ <b>Добро пожаловать в EliteStars!</b>", reply_markup=get_main_menu(), parse_mode="HTML")
    else:
        sponsors = get_sponsors()
        markup = types.InlineKeyboardMarkup()
        for i, s in enumerate(sponsors, 1): markup.add(types.InlineKeyboardButton(f"⭐️ Канал №{i}", url=s[1]))
        markup.add(types.InlineKeyboardButton("✅ Я подписался", callback_data="sub_check"))
        bot.send_message(message.chat.id, "⚠️ <b>Подпишитесь на каналы для входа:</b>", reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    uid = call.from_user.id
    update_activity(uid)
    
    user_status = db_query("SELECT is_banned FROM users WHERE user_id = ?", (uid,))
    if user_status and user_status[0][0] == 1:
        bot.answer_callback_query(call.id, "🚫 Бан!", show_alert=True)
        return

    if call.data.startswith("adm_"):
        if uid not in ADMIN_IDS: return
        action = call.data.split("_")[1]
        try:
            target_uid = int(call.message.text.split("ID ")[1].split("\n")[0])
            if action == "ok":
                bot.edit_message_text(call.message.text.replace("🔄 Статус: Ожидает обработки ⚙️", "✅ <b>Выплачено 🎁</b>"), call.message.chat.id, call.message.message_id, parse_mode="HTML")
                bot.send_message(target_uid, "🎁 <b>Заявка одобрена!</b>", parse_mode="HTML")
            elif action == "no":
                bot.edit_message_text(call.message.text.replace("🔄 Статус: Ожидает обработки ⚙️", "❌ <b>Отклонено</b>"), call.message.chat.id, call.message.message_id, parse_mode="HTML")
                bot.send_message(target_uid, "❌ <b>Заявка отклонена.</b>", parse_mode="HTML")
        except: pass
        return

    if call.data == "sub_check":
        if check_sub(uid):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "✅ <b>Доступ разрешен!</b>", reply_markup=get_main_menu(), parse_mode="HTML")
        else: bot.answer_callback_query(call.id, "❌ Подпишитесь на все каналы!", show_alert=True)
        return

    res = db_query("SELECT balance, referrals, last_bonus, username FROM users WHERE user_id = ?", (uid,))
    if not res: return
    balance, refs, last_bonus, u_name = res[0]
if call.data == "main_menu":
        bot.edit_message_text("✨ <b>Меню EliteStars:</b>", call.message.chat.id, call.message.message_id, reply_markup=get_main_menu(), parse_mode="HTML")
    elif call.data == "profile":
        bot.edit_message_text(f"👤 <b>Профиль:</b>\n👤 @{u_name}\n🆔 ID: <code>{uid}</code>\n💰 Баланс: {balance:.2f} ⭐️\n👥 Рефералы: {refs}", call.message.chat.id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")), parse_mode="HTML")
    elif call.data == "earn":
        bot.edit_message_text(f"🌟 <b>Ссылка:</b>\n<code>https://t.me/{(bot.get_me().username)}?start={uid}</code>\n\n+5 ⭐️ за друга!", call.message.chat.id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")), parse_mode="HTML")
    elif call.data == "bonus":
        now = int(time.time())
        if now - last_bonus >= 86400:
            db_query("UPDATE users SET balance = balance + 1, last_bonus = ? WHERE user_id = ?", (now, uid))
            bot.answer_callback_query(call.id, "🎁 +1 ⭐️!", show_alert=True)
        else: bot.answer_callback_query(call.id, "⏰ Приходите завтра!", show_alert=True)
    elif call.data == "top":
        top = db_query("SELECT username, referrals FROM users ORDER BY referrals DESC LIMIT 10")
        text = "🏆 <b>ТОП 10:</b>\n\n"
        for i, u in enumerate(top, 1): text += f"{i}. @{u[0]} — {u[1]} реф.\n"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")), parse_mode="HTML")
    elif call.data == "promo":
        msg = bot.send_message(call.message.chat.id, "🎁 <b>Введите промокод:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_promo)
    elif call.data == "withdraw_menu":
        bot.edit_message_text("💳 <b>Выберите сумму для вывода:</b>", call.message.chat.id, call.message.message_id, reply_markup=get_withdraw_keyboard(), parse_mode="HTML")
    elif call.data.startswith("wd_"):
        amount = int(call.data.split("_")[1])
        if balance >= amount:
            pay_text = f"🌟 <b>Новая заявка!</b>\n👤 ID <code>{uid}</code>\n💰 Сумма: <b>{amount} ⭐️</b>\n🔄 Статус: Ожидает обработки ⚙️"
            m = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("✅ Одобрить", callback_data="adm_ok"), types.InlineKeyboardButton("❌ Отклонить", callback_data="adm_no"))
            bot.send_message(PAYMENT_CHANNEL_ID, pay_text, reply_markup=m, parse_mode="HTML")
            db_query("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, uid))
            bot.answer_callback_query(call.id, "✅ Заявка создана!", show_alert=True)
        else: bot.answer_callback_query(call.id, "❌ Недостаточно звёзд!", show_alert=True)

if name == 'main':
    init_db()
    print("EliteStars запущен! Система динамических промокодов активна.")
    
    # Бесконечный цикл для защиты от вылетов интернета
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Ошибка сети: {e}. Повторное подключение через 5 секунд...")
            time.sleep(5)
