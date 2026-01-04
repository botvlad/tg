{\rtf1\ansi\ansicpg1251\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import telebot\
from telebot import types\
import sqlite3\
import time\
import os\
from flask import Flask\
from threading import Thread\
\
# --- \uc0\u1053 \u1040 \u1057 \u1058 \u1056 \u1054 \u1049 \u1050 \u1048  FLASK \u1044 \u1051 \u1071  RENDER ---\
app = Flask('')\
\
@app.route('/')\
def home():\
    return "\uc0\u1041 \u1086 \u1090  \u1072 \u1082 \u1090 \u1080 \u1074 \u1077 \u1085 !"\
\
def run():\
    # Render \uc0\u1080 \u1089 \u1087 \u1086 \u1083 \u1100 \u1079 \u1091 \u1077 \u1090  \u1087 \u1086 \u1088 \u1090  10000 \u1087 \u1086  \u1091 \u1084 \u1086 \u1083 \u1095 \u1072 \u1085 \u1080 \u1102  \u1080 \u1083 \u1080  \u1073 \u1077 \u1088 \u1077 \u1090  \u1080 \u1079  \u1087 \u1077 \u1088 \u1077 \u1084 \u1077 \u1085 \u1085 \u1086 \u1081  \u1089 \u1088 \u1077 \u1076 \u1099 \
    port = int(os.environ.get("PORT", 8080))\
    app.run(host='0.0.0.0', port=port)\
\
def keep_alive():\
    t = Thread(target=run)\
    t.start()\
\
# --- \uc0\u1058 \u1042 \u1054 \u1049  \u1050 \u1054 \u1044  \u1041 \u1054 \u1058 \u1040  ---\
TOKEN = "8310349633:AAGtW1gAeSmdohMVaCOEcz73Ef7tIkbUNSQ"\
bot = telebot.TeleBot(TOKEN)\
\
ADMIN_IDS = [8063642030, 8453400444] \
PAYMENT_CHANNEL_ID = "@EliteStarsD" \
\
def db_query(sql, params=()):\
    with sqlite3.connect('bot_database.db', check_same_thread=False) as conn:\
        cursor = conn.cursor()\
        cursor.execute(sql, params)\
        res = cursor.fetchall()\
        conn.commit()\
        return res\
\
def init_db():\
    db_query('''CREATE TABLE IF NOT EXISTS users (\
        user_id INTEGER PRIMARY KEY, \
        username TEXT, \
        balance REAL DEFAULT 0, \
        last_bonus INTEGER DEFAULT 0,\
        referrals INTEGER DEFAULT 0,\
        referrer_id INTEGER DEFAULT 0,\
        is_activated INTEGER DEFAULT 0,\
        is_banned INTEGER DEFAULT 0,\
        last_seen INTEGER DEFAULT 0)''')\
    \
    db_query('''CREATE TABLE IF NOT EXISTS sponsors (\
        channel_id TEXT PRIMARY KEY, \
        link TEXT)''')\
\
    db_query('''CREATE TABLE IF NOT EXISTS promo_codes (\
        code TEXT PRIMARY KEY, \
        reward REAL, \
        uses_left INTEGER)''')\
    \
    db_query('''CREATE TABLE IF NOT EXISTS used_promos (\
        user_id INTEGER, \
        code TEXT,\
        PRIMARY KEY(user_id, code))''')\
\
# --- \uc0\u1058 \u1059 \u1058  \u1044 \u1054 \u1051 \u1046 \u1053 \u1067  \u1041 \u1067 \u1058 \u1068  \u1058 \u1042 \u1054 \u1048  \u1054 \u1041 \u1056 \u1040 \u1041 \u1054 \u1058 \u1063 \u1048 \u1050 \u1048  (Handler) ---\
# \uc0\u1071  \u1076 \u1086 \u1073 \u1072 \u1074 \u1080 \u1083  \u1090 \u1086 \u1083 \u1100 \u1082 \u1086  \u1073 \u1072 \u1079 \u1086 \u1074 \u1099 \u1081  \u1089 \u1090 \u1072 \u1088 \u1090 , \u1095 \u1090 \u1086 \u1073 \u1099  \u1082 \u1086 \u1076  \u1073 \u1099 \u1083  \u1088 \u1072 \u1073 \u1086 \u1095 \u1080 \u1084 . \
# \uc0\u1042 \u1089 \u1090 \u1072 \u1074 \u1100  \u1089 \u1102 \u1076 \u1072  \u1074 \u1089 \u1077  \u1092 \u1091 \u1085 \u1082 \u1094 \u1080 \u1080  (def) \u1080 \u1079  \u1089 \u1074 \u1086 \u1077 \u1075 \u1086  \u1092 \u1072 \u1081 \u1083 \u1072  botfail.txt!\
\
@bot.message_handler(commands=['start'])\
def start(message):\
    init_user(message.from_user.id, message.from_user.username)\
    bot.send_message(message.chat.id, "\uc0\u1055 \u1088 \u1080 \u1074 \u1077 \u1090 ! \u1041 \u1086 \u1090  \u1079 \u1072 \u1087 \u1091 \u1097 \u1077 \u1085  \u1085 \u1072  Render \u1080  \u1088 \u1072 \u1073 \u1086 \u1090 \u1072 \u1077 \u1090  24/7.")\
\
def init_user(uid, username):\
    user = db_query("SELECT * FROM users WHERE user_id = ?", (uid,))\
    if not user:\
        db_query("INSERT INTO users (user_id, username) VALUES (?, ?)", (uid, username))\
\
# (\uc0\u1054 \u1089 \u1090 \u1072 \u1083 \u1100 \u1085 \u1086 \u1081  \u1090 \u1074 \u1086 \u1081  \u1082 \u1086 \u1076  \u1080 \u1079  \u1092 \u1072 \u1081 \u1083 \u1072  \u1074 \u1089 \u1090 \u1072 \u1074 \u1100  \u1089 \u1102 \u1076 \u1072  \u1087 \u1077 \u1088 \u1077 \u1076  \u1073 \u1083 \u1086 \u1082 \u1086 \u1084  \u1079 \u1072 \u1087 \u1091 \u1089 \u1082 \u1072  \u1085 \u1080 \u1078 \u1077 )\
\
if __name__ == "__main__":\
    init_db()\
    keep_alive() # \uc0\u1047 \u1072 \u1087 \u1091 \u1089 \u1082  \u1074 \u1077 \u1073 -\u1089 \u1077 \u1088 \u1074 \u1077 \u1088 \u1072  \u1076 \u1083 \u1103  Render\
    print("\uc0\u1041 \u1086 \u1090  \u1079 \u1072 \u1087 \u1091 \u1097 \u1077 \u1085 ...")\
    bot.polling(none_stop=True)}
