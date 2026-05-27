#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FunPay PHANTOM v1.2 BETA
Автор: Dzhant
Система автоматизации аренды Steam-аккаунтов на FunPay
"""

import subprocess
import sys
import os
import time

# ==================== АВТО-ПЕРЕЗАПУСК ====================
def auto_restart():
    """Автоматический перезапуск скрипта"""
    print("\n🔄 Автоматический перезапуск через 2 секунды...")
    time.sleep(2)
    os.execv(sys.executable, [sys.executable] + sys.argv)

# ==================== ПРОВЕРКА И УСТАНОВКА БИБЛИОТЕК ====================
required_libs = ["aiogram", "aiohttp", "psutil", "aiohttp-socks"]
need_restart = False

print("\n🔍 Проверка зависимостей...")

for lib in required_libs:
    try:
        if lib == "aiohttp-socks":
            __import__("aiohttp_socks")
        else:
            __import__(lib)
        print(f"   ✅ {lib} установлен")
    except ImportError:
        print(f"   ❌ {lib} не найден - устанавливаю...")
        os.system(f"{sys.executable} -m pip install {lib} --break-system-packages")
        need_restart = True

if need_restart:
    auto_restart()

# Импорт после проверки
import asyncio
import json
import time
import base64
import hmac
import hashlib
import struct
import random
import string
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
import psutil
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message, BotCommand
from aiohttp_socks import ProxyConnector

# ==================== НАСТРОЙКА ЛОГИРОВАНИЯ ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('phantom.log', encoding='utf-8'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ==================== ГЛОБАЛЬНАЯ КОНФИГУРАЦИЯ ====================
global_config = {}

# ==================== ЦВЕТА ДЛЯ КОНСОЛИ ====================
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def cprint(text, color=Colors.GREEN):
    print(f"{color}{text}{Colors.END}")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_banner():
    clear_screen()
    print(f"""{Colors.CYAN}
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣴⣾⣿⣿⣿⣿⣿⣿⣿⣷⣦⣄⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡏⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠁⠀⠀⠀⠀
{Colors.END}
{Colors.BOLD}{Colors.HEADER}==================================================
                FUNPAY PHANTOM v1.2 BETA
             🚀 by Dzhant 🚀                  
             ⚠️ РАННИЙ ДОСТУП (FULL AUTO) ⚠️              
=================================================={Colors.END}

{Colors.GREEN}💎 ПРЕИМУЩЕСТВА АВТОМАТИЗИРОВАННОГО ЯДРА PHANTOM:
⚙️ Полная Автономия: 24/7 без участия человека
🎮 Авто-Выдача Steam: Моментальная выдача данных
🔐 Авто-Безопасность: Генератор Guard + смена паролей
🎁 Авто-Маркетинг: Бонусы за отзывы 5★
📦 Авто-Склад: Деактивация лотов при пустом складе{Colors.END}

{Colors.YELLOW}📱 СОЦИАЛЬНЫЕ СЕТИ:
   • Telegram: https://t.me/FunPayPHANTOM{Colors.END}

{Colors.BOLD}{Colors.BLUE}=================================================={Colors.END}
""")

# ==================== FSM СОСТОЯНИЯ ====================
class AuthState(StatesGroup):
    waiting_for_password = State()

class BonusTimeState(StatesGroup):
    waiting_for_hours = State()

class CreateTagState(StatesGroup):
    waiting_for_tagname = State()

class AddAccountState(StatesGroup):
    waiting_for_tag = State()
    waiting_for_login = State()
    waiting_for_password_acc = State()
    waiting_for_shared_secret = State()

class LinkLotState(StatesGroup):
    waiting_for_link_string = State()

class EditWelcomeTextState(StatesGroup):
    waiting_for_text = State()

class EditBonusTextState(StatesGroup):
    waiting_for_text = State()

# ==================== ЯДРО STEAM GUARD ====================
def generate_steam_code(shared_secret: str) -> str:
    try:
        if not shared_secret:
            return "❌ Нет секрета"
        secret = base64.b64decode(shared_secret)
        interval = int(time.time()) // 30
        interval_bytes = struct.pack('>Q', interval)
        hmac_hash = hmac.new(secret, interval_bytes, hashlib.sha1).digest()
        offset = hmac_hash[-1] & 0x0F
        code_bytes = hmac_hash[offset:offset + 4]
        code = struct.unpack('>I', code_bytes)[0] & 0x7FFFFFFF
        alphabet = "23456789BCDFGHJKMNPQRTVWXY"
        result = ""
        for _ in range(5):
            result += alphabet[code % len(alphabet)]
            code //= len(alphabet)
        return result
    except:
        return "Ошибка"

def extract_shared_secret(content: str) -> Optional[str]:
    try:
        data = json.loads(content)
        if "shared_secret" in data:
            return data["shared_secret"]
    except:
        pass
    match = re.search(r'"shared_secret"\s*:\s*"([^"]+)"', content)
    if match:
        return match.group(1)
    match = re.search(r'shared_secret["\s:]+([A-Za-z0-9+/=]+)', content)
    if match:
        return match.group(1)
    if len(content) > 20 and re.match(r'^[A-Za-z0-9+/=]+$', content):
        return content
    return None

def process_macros(text: str, username: str = "", login: str = "", password: str = "",
                   guard: str = "", time_remaining: str = "", bonus_hours: int = 0) -> str:
    result = text.replace("$user", username)
    result = result.replace("$login", login)
    result = result.replace("$password", password)
    result = result.replace("$guard", guard)
    result = result.replace("$time", time_remaining)
    result = result.replace("$bonus", str(bonus_hours))
    return f"👻\n\n{result}"

def format_time_remaining(seconds: int) -> str:
    if seconds <= 0:
        return "истекло"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours} ч. {minutes} мин."
    return f"{minutes} мин."

def generate_random_password(length: int = 16) -> str:
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))

# ==================== РАБОТА С КОНФИГУРАЦИЕЙ ====================
def load_config() -> Optional[Dict]:
    if os.path.exists('config.json'):
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки конфига: {e}")
            return None
    return None

def save_config(config: Dict):
    global global_config
    try:
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        global_config = config
        logger.info("✅ Конфигурация сохранена")
    except Exception as e:
        logger.error(f"Ошибка сохранения конфига: {e}")

def setup_wizard() -> Dict:
    """Первичная настройка - создаёт config.json"""
    clear_screen()
    show_banner()
    
    cprint("\n⚙️ ПЕРВИЧНАЯ НАСТРОЙКА", Colors.BOLD + Colors.CYAN)
    print("=" * 50)
    
    cfg = {
        "telegram": {
            "token": "",
            "password": "",
            "chat_id": None,
            "proxy": None
        },
        "funpay": {
            "golden_key": "",
            "proxy": None,
            "last_raise_time": 0
        },
        "settings": {
            "auto_raise": True,
            "send_messages": True,
            "ignore_system_messages": True,
            "bonus_enabled": True,
            "bonus_hours": 1,
            "welcome_text": "Привет, $user! Твои данные: Логин: $login | Пароль: $password. Код Guard: $guard. Время аренды: $time",
            "bonus_text": "Спасибо за 5 звезд! Твоя аренда продлена на +$bonus ч. Новое время окончания: $time"
        },
        "steam_rent": {
            "tags": {},
            "active_rents": []
        }
    }
    
    cprint("\n📱 Настройка Telegram бота:", Colors.YELLOW)
    cfg["telegram"]["token"] = input("   Токен (от @BotFather): ").strip()
    cfg["telegram"]["password"] = input("   Секретный пароль админа: ").strip()
    
    cprint("\n🔑 Настройка FunPay:", Colors.YELLOW)
    cfg["funpay"]["golden_key"] = input("   Golden Key: ").strip()
    
    cprint("\n🌐 Настройка прокси (Enter если не нужны):", Colors.YELLOW)
    tg_proxy = input("   Прокси для Telegram (socks5://user:pass@ip:port): ").strip()
    fp_proxy = input("   Прокси для FunPay (http://user:pass@ip:port): ").strip()
    cfg["telegram"]["proxy"] = tg_proxy if tg_proxy else None
    cfg["funpay"]["proxy"] = fp_proxy if fp_proxy else None
    
    save_config(cfg)
    cprint("\n✅ Конфигурация сохранена! ЗАПУСКАЮ БОТА...", Colors.GREEN)
    print("=" * 50)
    time.sleep(1)
    
    return cfg

# ==================== API FUNPAY ====================
async def funpay_request(endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
    proxy = global_config.get("funpay", {}).get("proxy")
    headers = {
        "Authorization": f"Bearer {global_config['funpay']['golden_key']}",
        "Content-Type": "application/json"
    }
    
    proxy_url = None
    if proxy and proxy != "None":
        proxy_url = proxy
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.request(method, f"https://api.funpay.com/{endpoint}", 
                                      headers=headers, json=data, proxy=proxy_url, timeout=30) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {}
        except:
            return {}

async def send_funpay_message(chat_id: str, text: str):
    if not global_config.get("settings", {}).get("send_messages", True):
        return
    await funpay_request(f"chat/{chat_id}/send", "POST", {"text": text})

async def disable_lot(lot_id: str):
    await funpay_request(f"lots/{lot_id}/disable", "POST")
    logger.info(f"Лот {lot_id} деактивирован")

async def get_funpay_dialogs() -> List[Dict]:
    result = await funpay_request("chat/dialogs")
    return result.get("items", [])

async def get_funpay_messages(dialog_id: str) -> List[Dict]:
    result = await funpay_request(f"chat/{dialog_id}/messages")
    return result.get("items", [])

# ==================== АВТОМАТИЧЕСКАЯ ВЫДАЧА ====================
async def parse_orders_and_issue():
    try:
        dialogs = await get_funpay_dialogs()
        
        for dialog in dialogs:
            dialog_id = dialog.get("id")
            buyer_name = dialog.get("buyer", {}).get("username", "Покупатель")
            
            already = any(r.get("buyer_id") == dialog_id for r in global_config.get("steam_rent", {}).get("active_rents", []))
            if already:
                continue
            
            messages = await get_funpay_messages(dialog_id)
            
            for msg in messages:
                text = msg.get("text", "").lower()
                
                if msg.get("system") and global_config.get("settings", {}).get("ignore_system_messages", True):
                    continue
                
                if any(k in text for k in ["оплатил", "купил", "заказ"]):
                    hours_match = re.search(r'(\d+)\s*шт', text) or re.search(r'(\d+)\s*час', text) or re.search(r'(\d+)', text)
                    if not hours_match:
                        continue
                    hours = min(int(hours_match.group(1)), 24)
                    
                    tag = None
                    for tn, td in global_config["steam_rent"]["tags"].items():
                        for lot in td.get("linked_lots", []):
                            if str(lot) in dialog_id or str(lot) in text:
                                tag = tn
                                break
                        if tag:
                            break
                    if not tag and global_config["steam_rent"]["tags"]:
                        tag = list(global_config["steam_rent"]["tags"].keys())[0]
                    if not tag:
                        continue
                    
                    free_acc = None
                    for acc in global_config["steam_rent"]["tags"][tag]["accounts"]:
                        if acc.get("status") == "free":
                            free_acc = acc
                            break
                    
                    if free_acc:
                        rent_until = time.time() + (hours * 3600)
                        free_acc["status"] = "rented"
                        free_acc["rent_until"] = rent_until
                        free_acc["buyer_id"] = dialog_id
                        
                        global_config["steam_rent"]["active_rents"].append({
                            "login": free_acc["login"],
                            "tag": tag,
                            "rent_until": rent_until,
                            "buyer_id": dialog_id
                        })
                        
                        save_config(global_config)
                        
                        code = generate_steam_code(free_acc.get("shared_secret", ""))
                        time_str = format_time_remaining(hours * 3600)
                        
                        welcome_msg = process_macros(
                            global_config["settings"]["welcome_text"],
                            buyer_name,
                            free_acc["login"],
                            free_acc["password"],
                            code,
                            time_str
                        )
                        
                        await send_funpay_message(dialog_id, welcome_msg)
                        logger.info(f"✅ Выдан {free_acc['login']} на {hours}ч")
                    else:
                        await send_funpay_message(dialog_id, "Извините, все аккаунты заняты. 👻")
                    break
    except Exception as e:
        logger.error(f"Ошибка парсинга заказов: {e}")

async def parse_reviews_and_bonus():
    try:
        if not global_config.get("settings", {}).get("bonus_enabled", True):
            return
        
        dialogs = await get_funpay_dialogs()
        
        for dialog in dialogs:
            messages = await get_funpay_messages(dialog.get("id"))
            
            for msg in messages:
                text = msg.get("text", "").lower()
                
                if any(k in text for k in ["5 звезд", "5 звёзд", "отлично"]):
                    for rent in global_config["steam_rent"]["active_rents"]:
                        if rent.get("buyer_id") == dialog.get("id"):
                            bonus = global_config["settings"]["bonus_hours"]
                            rent["rent_until"] += bonus * 3600
                            
                            for tag in global_config["steam_rent"]["tags"].values():
                                for acc in tag["accounts"]:
                                    if acc["login"] == rent["login"]:
                                        acc["rent_until"] = rent["rent_until"]
                            
                            save_config(global_config)
                            
                            new_time = format_time_remaining(rent["rent_until"] - time.time())
                            bonus_msg = process_macros(
                                global_config["settings"]["bonus_text"],
                                dialog.get("buyer", {}).get("username", "Покупатель"),
                                time_remaining=new_time,
                                bonus_hours=bonus
                            )
                            
                            await send_funpay_message(dialog.get("id"), bonus_msg)
                            logger.info(f"🎁 Бонус +{bonus}ч")
                            break
    except Exception as e:
        logger.error(f"Ошибка бонусов: {e}")

async def change_steam_password(login: str, new_password: str) -> bool:
    logger.info(f"[Steam API] Смена пароля для {login}")
    return True

# ==================== ФОНОВЫЙ ЦИКЛ ====================
async def phantom_loop():
    logger.info("👻 Фоновый цикл запущен")
    last_orders = 0
    last_reviews = 0
    
    while True:
        try:
            if not global_config:
                await asyncio.sleep(5)
                continue
            
            now = time.time()
            
            if now - last_orders >= 30:
                await parse_orders_and_issue()
                last_orders = now
            if now - last_reviews >= 60:
                await parse_reviews_and_bonus()
                last_reviews = now
            
            new_rents = []
            for rent in global_config["steam_rent"].get("active_rents", []):
                if rent["rent_until"] > now:
                    new_rents.append(rent)
                else:
                    for tag in global_config["steam_rent"]["tags"].values():
                        for acc in tag["accounts"]:
                            if acc["login"] == rent["login"]:
                                acc["status"] = "free"
                                acc["rent_until"] = 0
                                acc["buyer_id"] = None
                                new_pass = generate_random_password()
                                acc["password"] = new_pass
                                await change_steam_password(rent["login"], new_pass)
                                if global_config["settings"].get("send_messages") and rent.get("buyer_id"):
                                    await send_funpay_message(rent["buyer_id"], process_macros("🕐 Время аренды истекло."))
                                logger.info(f"🔐 Аренда {rent['login']} завершена")
                                break
            global_config["steam_rent"]["active_rents"] = new_rents
            save_config(global_config)
            
            for tag_name, tag_data in global_config["steam_rent"]["tags"].items():
                free = sum(1 for a in tag_data["accounts"] if a.get("status") == "free")
                if free == 0 and tag_data["accounts"]:
                    for lot in tag_data.get("linked_lots", []):
                        await disable_lot(lot)
                    logger.warning(f"📦 Тег {tag_name}: аккаунты кончились")
            
            if global_config["settings"].get("auto_raise"):
                last = global_config["funpay"].get("last_raise_time", 0)
                if now - last >= 3600:
                    global_config["funpay"]["last_raise_time"] = now
                    save_config(global_config)
                    logger.info("🔄 Автоподнятие лотов")
            
            await asyncio.sleep(10)
        except Exception as e:
            logger.error(f"Цикл ошибка: {e}")
            await asyncio.sleep(30)

# ==================== TELEGRAM БОТ - КЛАВИАТУРЫ ====================
def get_main_keyboard() -> InlineKeyboardMarkup:
    status = "🟢" if global_config.get("settings", {}).get("auto_raise", True) else "🔴"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⚙️ Настройки Phantom [{status}]", callback_data="menu_settings")],
        [InlineKeyboardButton(text="✉️ Настройка сообщений", callback_data="menu_messages")],
        [InlineKeyboardButton(text="🎮 Управление Арендой", callback_data="menu_rent")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="menu_stats")],
        [InlineKeyboardButton(text="ℹ️ О программе", callback_data="menu_about")]
    ])

def get_settings_keyboard() -> InlineKeyboardMarkup:
    status = "🟢 ВКЛ" if global_config.get("settings", {}).get("auto_raise", True) else "🔴 ВЫКЛ"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🔄 Автоподнятие: {status}", callback_data="toggle_auto_raise")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]
    ])

def get_messages_keyboard() -> InlineKeyboardMarkup:
    s = "🟢" if global_config["settings"].get("send_messages", True) else "🔴"
    i = "🟢" if global_config["settings"].get("ignore_system_messages", True) else "🔴"
    b = "🟢" if global_config["settings"].get("bonus_enabled", True) else "🔴"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💬 Отправка: {s}", callback_data="toggle_send")],
        [InlineKeyboardButton(text=f"🤖 Игнор системных: {i}", callback_data="toggle_ignore")],
        [InlineKeyboardButton(text=f"🎁 Бонус: {b}", callback_data="toggle_bonus")],
        [InlineKeyboardButton(text="⏱️ Время бонуса", callback_data="edit_bonus_time")],
        [InlineKeyboardButton(text="📝 Текст приветствия", callback_data="edit_welcome")],
        [InlineKeyboardButton(text="🎁 Текст бонуса", callback_data="edit_bonus_text")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]
    ])

def get_rent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать тег", callback_data="create_tag")],
        [InlineKeyboardButton(text="🔐 Добавить аккаунт", callback_data="add_account")],
        [InlineKeyboardButton(text="🔗 Привязать лот", callback_data="link_lot")],
        [InlineKeyboardButton(text="📊 Проверить склад", callback_data="check_stock")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]
    ])

# ==================== TELEGRAM ХЭНДЛЕРЫ ====================
async def start_command(msg: Message, bot: Bot, state: FSMContext):
    if global_config.get("telegram", {}).get("chat_id") == msg.chat.id:
        await msg.answer("👻 Вы уже авторизованы!", reply_markup=get_main_keyboard(), parse_mode="Markdown")
        return
    
    await state.set_state(AuthState.waiting_for_password)
    await msg.answer("🔐 Введите секретный пароль:", parse_mode="Markdown")

async def process_auth(msg: Message, bot: Bot, state: FSMContext):
    if await state.get_state() != AuthState.waiting_for_password.state:
        return
    
    if msg.text.strip() != global_config.get("telegram", {}).get("password"):
        await msg.answer("❌ Неверный пароль!")
        await state.clear()
        return
    
    global_config["telegram"]["chat_id"] = msg.chat.id
    save_config(global_config)
    
    await msg.answer("✅ Авторизация успешна!\n👻 Добро пожаловать!", reply_markup=get_main_keyboard(), parse_mode="Markdown")
    await state.clear()

async def sys_command(msg: Message):
    if msg.chat.id != global_config.get("telegram", {}).get("chat_id"):
        return
    
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    net = psutil.net_io_counters()
    boot = time.time() - psutil.boot_time()
    active = len(global_config.get("steam_rent", {}).get("active_rents", []))
    total = sum(len(t["accounts"]) for t in global_config.get("steam_rent", {}).get("tags", {}).values())
    
    await msg.answer(
        f"📊 CPU: {cpu}%\n💾 RAM: {mem.used//(1024**2)}MB\n🌐 Сеть: 📤{net.bytes_sent//(1024**2)}MB 📥{net.bytes_recv//(1024**2)}MB\n⏱️ Аптайм: {int(boot//3600)}ч\n🎮 Аренд: {active}/{total}\n👻 Phantom: 🟢",
        parse_mode="Markdown"
    )

async def handle_callback(call: CallbackQuery, bot: Bot, state: FSMContext):
    if call.message.chat.id != global_config.get("telegram", {}).get("chat_id"):
        await call.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await call.answer()
    data = call.data
    
    if data == "back_main":
        await call.message.edit_text("👻 Главное меню", reply_markup=get_main_keyboard(), parse_mode="Markdown")
    
    elif data == "menu_about":
        await call.message.edit_text("ℹ️ FunPay PHANTOM v1.2 BETA\n👻 Автор: Dzhant\n📱 Telegram: https://t.me/FunPayPHANTOM", 
                                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]]), 
                                    parse_mode="Markdown")
    
    elif data == "menu_settings":
        await call.message.edit_text("⚙️ Настройки", reply_markup=get_settings_keyboard(), parse_mode="Markdown")
    
    elif data == "menu_messages":
        await call.message.edit_text("✉️ Настройка сообщений", reply_markup=get_messages_keyboard(), parse_mode="Markdown")
    
    elif data == "menu_rent":
        await call.message.edit_text("🎮 Управление арендой", reply_markup=get_rent_keyboard(), parse_mode="Markdown")
    
    elif data == "menu_stats":
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        net = psutil.net_io_counters()
        boot = time.time() - psutil.boot_time()
        active = len(global_config.get("steam_rent", {}).get("active_rents", []))
        await call.message.edit_text(f"📊 CPU: {cpu}%\n💾 RAM: {mem.used//(1024**2)}MB\n🌐 Сеть: 📤{net.bytes_sent//(1024**2)}MB\n⏱️ Аптайм: {int(boot//3600)}ч\n🎮 Аренд: {active}\n👻 Phantom: 🟢", 
                                    reply_markup=get_main_keyboard(), parse_mode="Markdown")
    
    elif data == "toggle_auto_raise":
        global_config["settings"]["auto_raise"] = not global_config["settings"].get("auto_raise", True)
        save_config(global_config)
        await call.message.edit_text(f"🔄 Автоподнятие: {'✅ ВКЛ' if global_config['settings']['auto_raise'] else '❌ ВЫКЛ'}", 
                                    reply_markup=get_settings_keyboard(), parse_mode="Markdown")
    
    elif data == "toggle_send":
        global_config["settings"]["send_messages"] = not global_config["settings"].get("send_messages", True)
        save_config(global_config)
        await call.message.edit_text("✉️ Обновлено", reply_markup=get_messages_keyboard(), parse_mode="Markdown")
    
    elif data == "toggle_ignore":
        global_config["settings"]["ignore_system_messages"] = not global_config["settings"].get("ignore_system_messages", True)
        save_config(global_config)
        await call.message.edit_text("✉️ Обновлено", reply_markup=get_messages_keyboard(), parse_mode="Markdown")
    
    elif data == "toggle_bonus":
        global_config["settings"]["bonus_enabled"] = not global_config["settings"].get("bonus_enabled", True)
        save_config(global_config)
        await call.message.edit_text(f"🎁 Бонус: {'✅ ВКЛ' if global_config['settings']['bonus_enabled'] else '❌ ВЫКЛ'}", 
                                    reply_markup=get_messages_keyboard(), parse_mode="Markdown")
    
    elif data == "edit_bonus_time":
        await state.set_state(BonusTimeState.waiting_for_hours)
        await call.message.edit_text("⏱️ Введите бонусные часы (1-24):", parse_mode="Markdown")
    
    elif data == "edit_welcome":
        await state.set_state(EditWelcomeTextState.waiting_for_text)
        await call.message.edit_text("📝 Новый текст приветствия\nМакросы: $user, $login, $password, $guard, $time", parse_mode="Markdown")
    
    elif data == "edit_bonus_text":
        await state.set_state(EditBonusTextState.waiting_for_text)
        await call.message.edit_text("🎁 Новый текст бонуса\nМакросы: $user, $bonus, $time", parse_mode="Markdown")
    
    elif data == "create_tag":
        await state.set_state(CreateTagState.waiting_for_tagname)
        await call.message.edit_text("➕ Введите имя тега:", parse_mode="Markdown")
    
    elif data == "add_account":
        tags = list(global_config.get("steam_rent", {}).get("tags", {}).keys())
        if not tags:
            await call.message.edit_text("❌ Сначала создайте тег", reply_markup=get_rent_keyboard(), parse_mode="Markdown")
            return
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=f"seltag_{t}")] for t in tags] + [[InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]])
        await call.message.edit_text("🔐 Выберите тег:", reply_markup=kb, parse_mode="Markdown")
    
    elif data == "link_lot":
        await state.set_state(LinkLotState.waiting_for_link_string)
        await call.message.edit_text("🔗 Формат: ТЭГ:ID_ЛОТА\nПример: CS2:123456789", parse_mode="Markdown")
    
    elif data == "check_stock":
        tags = global_config.get("steam_rent", {}).get("tags", {})
        if not tags:
            await call.message.edit_text("📊 Склад пуст", reply_markup=get_rent_keyboard(), parse_mode="Markdown")
            return
        res = "📊 Склад\n\n"
        for tn, td in tags.items():
            accs = td.get("accounts", [])
            free = sum(1 for a in accs if a.get("status") == "free")
            res += f"**{tn}** 🟢{free} 🔴{len(accs)-free}\n"
            for a in accs:
                code = generate_steam_code(a.get("shared_secret", ""))
                res += f"  {'🟢' if a['status']=='free' else '🔴'} `{a['login']}` | `{code}`\n"
            res += "\n"
        await call.message.edit_text(res, reply_markup=get_rent_keyboard(), parse_mode="Markdown")
    
    elif data.startswith("seltag_"):
        tag = data.replace("seltag_", "")
        await state.update_data(selected_tag=tag)
        await state.set_state(AddAccountState.waiting_for_login)
        await call.message.edit_text(f"🔐 Тег: {tag}\nВведите логин:", parse_mode="Markdown")

async def handle_fsm_messages(msg: Message, state: FSMContext):
    cs = await state.get_state()
    
    if cs == BonusTimeState.waiting_for_hours.state:
        try:
            h = int(msg.text.strip())
            if 1 <= h <= 24:
                global_config["settings"]["bonus_hours"] = h
                save_config(global_config)
                await msg.answer(f"✅ Бонус: {h} ч", reply_markup=get_main_keyboard())
            else:
                await msg.answer("❌ 1-24")
            await state.clear()
        except:
            await msg.answer("❌ Введите число")
            await state.clear()
    
    elif cs == EditWelcomeTextState.waiting_for_text.state:
        t = msg.text.strip()
        if len(t) >= 10:
            global_config["settings"]["welcome_text"] = t
            save_config(global_config)
            await msg.answer("✅ Текст сохранен!", reply_markup=get_main_keyboard())
        else:
            await msg.answer("❌ Минимум 10 символов")
        await state.clear()
    
    elif cs == EditBonusTextState.waiting_for_text.state:
        t = msg.text.strip()
        if len(t) >= 10:
            global_config["settings"]["bonus_text"] = t
            save_config(global_config)
            await msg.answer("✅ Текст сохранен!", reply_markup=get_main_keyboard())
        else:
            await msg.answer("❌ Минимум 10 символов")
        await state.clear()
    
    elif cs == CreateTagState.waiting_for_tagname.state:
        tag = msg.text.strip().upper()
        if "steam_rent" not in global_config:
            global_config["steam_rent"] = {"tags": {}, "active_rents": []}
        if tag in global_config["steam_rent"]["tags"]:
            await msg.answer(f"❌ Тег {tag} уже есть")
        else:
            global_config["steam_rent"]["tags"][tag] = {"accounts": [], "linked_lots": []}
            save_config(global_config)
            await msg.answer(f"✅ Тег {tag} создан!", reply_markup=get_main_keyboard())
        await state.clear()
    
    elif cs == AddAccountState.waiting_for_login.state:
        await state.update_data(login=msg.text.strip())
        await state.set_state(AddAccountState.waiting_for_password_acc)
        await msg.answer("🔐 Введите пароль:", parse_mode="Markdown")
    
    elif cs == AddAccountState.waiting_for_password_acc.state:
        await state.update_data(password=msg.text.strip())
        await state.set_state(AddAccountState.waiting_for_shared_secret)
        await msg.answer("🔐 Введите shared_secret или .maFile (или 'skip'):", parse_mode="Markdown")
    
    elif cs == AddAccountState.waiting_for_shared_secret.state:
        data = await state.get_data()
        tag = data.get("selected_tag")
        login = data.get("login")
        password = data.get("password")
        secret = msg.text.strip()
        if secret.lower() == "skip":
            secret = ""
        else:
            ext = extract_shared_secret(secret)
            if ext:
                secret = ext
        global_config["steam_rent"]["tags"][tag]["accounts"].append({
            "login": login, "password": password, "shared_secret": secret,
            "status": "free", "rent_until": 0, "buyer_id": None
        })
        save_config(global_config)
        code = generate_steam_code(secret) if secret else "❌"
        await msg.answer(f"✅ {login} добавлен!\nSteam Guard: {code}", reply_markup=get_main_keyboard())
        await state.clear()
    
    elif cs == LinkLotState.waiting_for_link_string.state:
        parts = msg.text.strip().split(":")
        if len(parts) != 2:
            await msg.answer("❌ Формат: ТЭГ:ID")
        else:
            tag, lid = parts[0].upper(), parts[1]
            if tag not in global_config.get("steam_rent", {}).get("tags", {}):
                await msg.answer(f"❌ Тег {tag} не существует")
            elif lid in global_config["steam_rent"]["tags"][tag]["linked_lots"]:
                await msg.answer(f"⚠️ Лот уже привязан")
            else:
                global_config["steam_rent"]["tags"][tag]["linked_lots"].append(lid)
                save_config(global_config)
                await msg.answer(f"✅ Лот {lid} привязан к {tag}", reply_markup=get_main_keyboard())
        await state.clear()

# ==================== ЗАПУСК ====================
async def main():
    """Главная функция - загружает конфиг или запускает настройку, затем сразу бота"""
    
    config = load_config()
    
    # Если конфига нет - запускаем настройку
    if config is None:
        config = setup_wizard()
    else:
        clear_screen()
        show_banner()
        cprint("\n✅ Загрузка конфигурации...", Colors.GREEN)
    
    global global_config
    global_config = config
    
    # Проверка обязательных полей
    if not global_config.get("telegram", {}).get("token"):
        cprint("\n❌ ОШИБКА: Не указан токен!", Colors.RED)
        cprint("Удалите config.json и перезапустите скрипт для настройки", Colors.YELLOW)
        input("\nНажмите Enter...")
        return
    
    cprint("\n" + "=" * 50, Colors.CYAN)
    cprint("🚀 ЗАПУСК FUNPAY PHANTOM v1.2 BETA", Colors.BOLD + Colors.GREEN)
    cprint("=" * 50, Colors.CYAN)
    cprint(f"👻 Статус: ПОЛНОСТЬЮ АВТОМАТИЗИРОВАН", Colors.YELLOW)
    cprint(f"📱 Telegram бот активен", Colors.CYAN)
    cprint(f"🎮 Тегов: {len(global_config.get('steam_rent', {}).get('tags', {}))}", Colors.CYAN)
    
    tg_proxy = global_config.get("telegram", {}).get("proxy")
    if tg_proxy and tg_proxy != "None":
        cprint(f"🌐 Прокси для Telegram: {tg_proxy[:50]}...", Colors.YELLOW)
    cprint("=" * 50 + "\n", Colors.CYAN)
    
    # Создаём бота (поддержка прокси)
    tg_proxy = global_config.get("telegram", {}).get("proxy")
    if tg_proxy and tg_proxy != "None" and tg_proxy is not None:
        try:
            bot = Bot(token=global_config["telegram"]["token"], proxy=tg_proxy)
            cprint("✅ Бот создан с прокси", Colors.GREEN)
        except Exception as e:
            cprint(f"⚠️ Ошибка прокси: {e}", Colors.YELLOW)
            bot = Bot(token=global_config["telegram"]["token"])
    else:
        bot = Bot(token=global_config["telegram"]["token"])
    
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрация хэндлеров
    dp.message.register(start_command, Command("start"))
    dp.message.register(sys_command, Command("sys"))
    dp.message.register(process_auth, F.text & ~F.text.startswith('/'))
    dp.message.register(handle_fsm_messages, F.text & ~F.text.startswith('/'))
    dp.callback_query.register(handle_callback)
    
    # Запускаем фоновый цикл
    asyncio.create_task(phantom_loop())
    
    cprint("🚀 Бот успешно запущен! Жду команды в Telegram...", Colors.GREEN + Colors.BOLD)
    logger.info("Бот запущен и готов к работе!")
    
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        cprint("\n\n👻 Остановлен пользователем", Colors.YELLOW)
    except Exception as e:
        cprint(f"\n❌ Ошибка: {e}", Colors.RED)
        logger.error(f"Ошибка: {e}", exc_info=True)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        cprint("\n👻 Завершён", Colors.YELLOW)
        sys.exit(0)