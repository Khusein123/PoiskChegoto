import requests
import time
import json
import os
import re
import telebot
import random
import string
from keep_alive import keep_alive

TOKEN = "7905547591:AAEivoneinmUDRtg7hvBkGPEPPAegMC36uc"
CHAT_ID = "5292727929"
bot = telebot.TeleBot(TOKEN)

OWNER_ID = 5292727929
authorized_users = {OWNER_ID}
valid_keys = set()
waiting_for_key = {}

SEARCH_INTERVAL = 60

def generate_key():
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    valid_keys.add(key)
    return key

def normalize_title(title):
    return re.sub(r"\s+", " ", title.lower())

def is_good_ad(title, description, price):
    bad_keywords = ["восстановлен", "реф", "рефаб", "не работает", "битый", "перекуп", "проблема", "треснут", "скол", "разбит"]
    good_keywords = ["идеал", "в отличном состоянии", "100% акб", "без царапин", "не вскрывался", "оригинал", "все работает"]
    full_text = f"{title} {description}".lower()

    if any(bad in full_text for bad in bad_keywords):
        return False
    if not any(good in full_text for good in good_keywords):
        return False
    return True

def check_for_new_ads(urls):
    headers = {"User-Agent": "Mozilla/5.0"}
    found_ads = []

    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.ok:
                matches = re.findall(r'{\"id\":\d+.*?}', response.text)
                for match in matches:
                    try:
                        ad = json.loads(match)
                        title = ad.get("title", "")
                        desc = ad.get("description", "")
                        price = int(ad.get("price", 0))
                        link = f"https://www.avito.ru{ad.get('url', '')}"
                        if is_good_ad(title, desc, price):
                            found_ads.append(f"📱 {title}\n💰 {price}₽\n🔗 {link}")
                    except:
                        continue
        except:
            continue
    return found_ads

@bot.message_handler(commands=["start"])
def start_cmd(msg):
    bot.send_message(msg.chat.id, "Привет! Используй /monitor <ссылки> для начала. Если у тебя нет доступа, введи ключ.")

@bot.message_handler(commands=["genkey"])
def genkey_cmd(msg):
    if msg.from_user.id == OWNER_ID:
        key = generate_key()
        bot.send_message(msg.chat.id, f"🔑 Твой ключ: `{key}`", parse_mode="Markdown")
    else:
        bot.send_message(msg.chat.id, "⛔ Недостаточно прав.")

@bot.message_handler(commands=["monitor"])
def monitor_cmd(msg):
    uid = msg.from_user.id
    if uid in authorized_users:
        urls = msg.text.split()[1:]
        if not urls:
            bot.send_message(msg.chat.id, "❗ Укажи хотя бы одну ссылку после команды.")
            return
        ads = check_for_new_ads(urls)
        if ads:
            for ad in ads:
                bot.send_message(msg.chat.id, ad)
        else:
            bot.send_message(msg.chat.id, "🔍 Объявлений не найдено.")
    else:
        bot.send_message(msg.chat.id, "🔐 Введите ключ доступа:")
        waiting_for_key[uid] = True

@bot.message_handler(func=lambda m: True)
def handle_text(msg):
    uid = msg.from_user.id
    if uid in waiting_for_key:
        if msg.text.strip().upper() in valid_keys:
            authorized_users.add(uid)
            del waiting_for_key[uid]
            bot.send_message(msg.chat.id, "✅ Доступ предоставлен! Теперь используй /monitor <ссылки>.")
        else:
            bot.send_message(msg.chat.id, "❌ Неверный ключ. Повторите ввод.")

keep_alive()
bot.polling(none_stop=True)
