import telebot
from telebot import types
import sqlite3
import time

# --- НАСТРОЙКИ ---
TOKEN = "ВАШ_ТОКЕН"  # Вставьте сюда свой токен
bot = telebot.TeleBot(TOKEN)

# Список ID техподдержки/запасных админов
ADMIN_IDS = [8063642030, 8453400444] 

# Никнейм ГЛАВНОГО ВЛАДЕЛЬЦА (без @)
OWNER_USERNAME = "EliteAdmin_ls"

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
    # Таблица пользователей (Добавили колонку role)
    db_query('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, 
        username TEXT, 
        balance REAL DEFAULT 0, 
        last_bonus INTEGER DEFAULT 0,
        referrals INTEGER DEFAULT 0,
        referrer_id INTEGER DEFAULT 0,
        is_activated INTEGER DEFAULT 0,
        is_banned INTEGER DEFAULT 0,
        last_seen INTEGER DEFAULT 0,
        role TEXT DEFAULT 'user')''') # user, admin, owner
    
    db_query('''CREATE TABLE IF NOT EXISTS sponsors (
        channel_id TEXT PRIMARY KEY, 
        link TEXT)''')

    db_query('''CREATE TABLE IF NOT EXISTS promocodes (
        code TEXT PRIMARY KEY, 
        amount REAL, 
        max_uses INTEGER, 
        current_uses INTEGER DEFAULT 0)''')
    
    db_query('''CREATE TABLE IF NOT EXISTS used_promos (
        user_id INTEGER, 
        code TEXT)''')
    
    # Спонсор по умолчанию
    check = db_query("SELECT count(*) FROM sponsors")
    if check[0][0] == 0:
        db_query("INSERT INTO sponsors (channel_id, link) VALUES (?, ?)", ("@EliteStarsH", "https://t.me/EliteStarsH"))

    # МИГРАЦИИ (Если база уже создана, добавляем новые колонки)
    try: db_query("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")
    except: pass
    try: db_query("ALTER TABLE users ADD COLUMN last_seen INTEGER DEFAULT 0")
    except: pass
    try: db_query("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
    except: pass

# --- ФУНКЦИИ ---
def update_activity(uid):
    db_query("UPDATE users SET last_seen = ? WHERE user_id = ?", (int(time.time()), uid))

def get_sponsors():
    return db_query("SELECT channel_id, link FROM sponsors")

# ПРОВЕРКА НА АДМИНА
def is_admin(user_id):
    # 1. Проверяем жесткий список
    if user_id in ADMIN_IDS:
        return True
    
    # 2. Проверяем базу данных
    res = db_query("SELECT role FROM users WHERE user_id = ?", (user_id,))
    if res and res[0][0] in ['admin', 'owner']:
        return True
    return False

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

# --- АДМИН ПАНЕЛЬ ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if is_admin(message.from_user.id): # Используем новую проверку
        update_activity(message.from_user.id)
        sponsors = get_sponsors()
        sp_text = "\n".join([f"🔹 {s[0]}" for s in sponsors])
        
        promos = db_query("SELECT code, amount, current_uses, max_uses FROM promocodes")
        pr_text = "\n".join([f"🎫 <code>{p[0]}</code> | {p[1]}⭐️ | {p[2]}/{p[3]}" for p in promos])
        
        text = (f"🛠 <b>Админ-панель EliteStars</b>\n\n"
                f"👤 Вы: <code>{message.from_user.id}</code>\n"
                f"🔑 Роль: {db_query('SELECT role FROM users WHERE user_id=?',(message.from_user.id,))[0][0]}\n\n"
                f"📡 <b>Спонсоры:</b>\n{sp_text if sp_text else 'Пусто'}\n"
                f"➕ <code>/add_sponsor @id link</code>\n"
                f"➖ <code>/del_sponsor @id</code>\n\n"
                f"🎫 <b>Промокоды:</b>\n{pr_text if pr_text else 'Нет активных'}\n"
                f"➕ <code>/add_promo КОД СУММА ЛИМИТ</code>\n"
                f"➖ <code>/del_promo КОД</code>\n\n"
                f"📊 <code>/stats</code> | 💰 <code>/give ID СУММА</code>\n"
                f"🚫 <code>/ban ID</code> | 🔓 <code>/unban ID</code>\n"
                f"👑 <code>/setadmin ID</code> — Назначить админа\n"
                f"📢 <code>/send ТЕКСТ</code> — Рассылка")
        bot.send_message(message.chat.id, text, parse_mode="HTML")

# Команда для назначения нового админа (доступна только владельцу или существующим админам)
@bot.message_handler(commands=['setadmin'])
def set_admin_cmd(message):
    if is_admin(message.from_user.id):
        try:
            target_id = int(message.text.split()[1])
            db_query("UPDATE users SET role = 'admin' WHERE user_id = ?", (target_id,))
            bot.send_message(message.chat.id, f"✅ Пользователь <code>{target_id}</code> теперь администратор!", parse_mode="HTML")
        except:
            bot.send_message(message.chat.id, "❌ Формат: <code>/setadmin 123456789</code>", parse_mode="HTML")

# Остальные админские команды (добавляем проверку is_admin везде)
@bot.message_handler(commands=['add_promo'])
def add_promo_cmd(message):
    if is_admin(message.from_user.id):
        try:
            parts = message.text.split()
            code, amount, limit = parts[1].upper(), float(parts[2]), int(parts[3])
            db_query("INSERT OR REPLACE INTO promocodes (code, amount, max_uses) VALUES (?, ?, ?)", (code, amount, limit))
            bot.send_message(message.chat.id, f"✅ Промокод {code} создан!")
        except: pass

@bot.message_handler(commands=['del_promo'])
def del_promo_cmd(message):
    if is_admin(message.from_user.id):
        try:
            code = message.text.split()[1].upper()
            db_query("DELETE FROM promocodes WHERE code = ?", (code,))
            bot.send_message(message.chat.id, f"🗑 Промокод {code} удален.")
        except: pass

@bot.message_handler(commands=['stats'])
def get_stats(message):
    if is_admin(message.from_user.id):
        now = int(time.time())
        limit = now - 900
        online = db_query("SELECT count(*) FROM users WHERE last_seen > ?", (limit,))[0][0]
        total = db_query("SELECT count(*) FROM users")[0][0]
        bot.send_message(message.chat.id, f"📊 <b>Статистика:</b>\n🟢 Онлайн: {online}\n👥 Всего: {total}", parse_mode="HTML")

@bot.message_handler(commands=['give'])
def give_stars(message):
    if is_admin(message.from_user.id):
        try:
            parts = message.text.split()
            tid, amount = int(parts[1]), float(parts[2])
            db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, tid))
            bot.send_message(message.chat.id, f"✅ Выдано {amount}⭐️ для {tid}")
        except: pass

# --- START (ИЗМЕНЕН) ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    uname = message.from_user.username if message.from_user.username else "User"
    update_activity(uid)
    
    # Регистрация
    user = db_query("SELECT is_banned FROM users WHERE user_id = ?", (uid,))
    if user and user[0][0] == 1:
        bot.send_message(message.chat.id, "🚫 Вы забанены.")
        return

    if not user:
        ref_id = 0
        args = message.text.split()
        if len(args) > 1:
            try:
                ref_id = int(args[1])
                if ref_id == uid: ref_id = 0
            except: pass
        
        # Определяем роль при регистрации
        role = 'user'
        if uname == OWNER_USERNAME: # Если ник совпадает с владельцем
            role = 'owner'
            bot.send_message(uid, "👑 <b>Владелец распознан! Права выданы.</b>", parse_mode="HTML")

        db_query("INSERT INTO users (user_id, username, referrer_id, is_activated, is_banned, last_seen, role) VALUES (?, ?, ?, 0, 0, ?, ?)", (uid, uname, ref_id, int(time.time()), role))
    
    else:
        # Если пользователь уже есть, но это владелец, обновим права
        if uname == OWNER_USERNAME:
            current_role = db_query("SELECT role FROM users WHERE user_id = ?", (uid,))[0][0]
            if current_role != 'owner':
                db_query("UPDATE users SET role = 'owner' WHERE user_id = ?", (uid,))
                bot.send_message(uid, "👑 <b>Владелец распознан! Права обновлены.</b>", parse_mode="HTML")

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

# Обязательный обработчик callback'ов (админка вывода)
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    uid = call.from_user.id
    if call.data.startswith("adm_"):
        # Проверяем права через is_admin()
        if not is_admin(uid): return 
        action = call.data.split("_")[1]
        try:
            # Парсим ID из текста сообщения (формат "👤 ID 12345")
            lines = call.message.text.split('\n')
            target_uid = 0
            for line in lines:
                if "ID" in line:
                    target_uid = int(line.split("ID")[1].strip().replace("<code>","").replace("</code>",""))
                    break
            
            if target_uid == 0: return # Не нашли ID

            if action == "ok":
                bot.edit_message_text(call.message.text.replace("🔄 Статус: Ожидает обработки ⚙️", "✅ <b>Выплачено 🎁</b>"), call.message.chat.id, call.message.message_id, parse_mode="HTML")
                try: bot.send_message(target_uid, "🎁 <b>Ваша заявка на вывод одобрена!</b>", parse_mode="HTML")
                except: pass
            elif action == "no":
                bot.edit_message_text(call.message.text.replace("🔄 Статус: Ожидает обработки ⚙️", "❌ <b>Отклонено</b>"), call.message.chat.id, call.message.message_id, parse_mode="HTML")
                # Возврат средств
                amount_line = [l for l in lines if "Сумма" in l][0]
                amount = int(amount_line.split(":")[1].replace("⭐️","").strip())
                db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, target_uid))
                try: bot.send_message(target_uid, f"❌ <b>Вывод отклонен. {amount} ⭐️ возвращены.</b>", parse_mode="HTML")
                except: pass
        except Exception as e: 
            print(f"Ошибка админки: {e}")
        return
    
    # ... Остальной код callback-ов (profile, earn, bonus и т.д. без изменений) ...
    # (Добавьте сюда стандартную логику из прошлого кода для обычных пользователей)

if __name__ == '__main__':
    init_db()
    print("Бот запущен. Ожидание владельца EliteAdmin_ls...")
    bot.polling(none_stop=True)
