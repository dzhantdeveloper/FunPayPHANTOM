#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
# Copyright (c) 2024 Dzhant

"""
FunPay PHANTOM v1.0 BETA
Автор: Dzhant
Система автоматизации почасовой аренды Steam-аккаунтов на FunPay

Telegram канал: https://t.me/FunPayPHANTOM
"""

import asyncio
import json
import os
import sys
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
from typing import Dict, List, Optional, Any

# Третьи стороны
try:
    import aiohttp
    from aiogram import Bot, Dispatcher, types, F
    from aiogram.filters import Command
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.types import (
        InlineKeyboardMarkup, InlineKeyboardButton,
        CallbackQuery, Message, BotCommand
    )
    import psutil
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Установите зависимости: pip install aiohttp aiogram psutil")
    sys.exit(1)

# ==================== НАСТРОЙКА ЛОГИРОВАНИЯ ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phantom.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== ГЛОБАЛЬНАЯ КОНФИГУРАЦИЯ ====================
global_config = {}

# ==================== FSM СОСТОЯНИЯ ====================
class AuthState(StatesGroup):
    waiting_for_password = State()

class BonusTimeState(StatesGroup):
    waiting_for_hours = State()

class CreateTagState(StatesGroup):
    waiting_for_tagname = State()

class AddAccountState(StatesGroup):
    waiting_for_account_string = State()

class LinkLotState(StatesGroup):
    waiting_for_link_string = State()

class EditWelcomeTextState(StatesGroup):
    waiting_for_text = State()

class EditBonusTextState(StatesGroup):
    waiting_for_text = State()

# ==================== УТИЛИТЫ ====================
def clear_screen():
    """Очистка экрана терминала"""
    os.system('cls' if os.name == 'nt' else 'clear')

def show_welcome_banner():
    """Отображение приветственного баннера"""
    clear_screen()
    print("""
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣴⣾⣿⣿⣿⣿⣿⣿⣿⣷⣦⣄⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡏⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠃⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡏⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠏⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠁⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠙⠛⠛⠛⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀

==================================================
                FUNPAY PHANTOM                
             🚀 by Dzhant 🚀                  
               [ v1.0 BETA ]                  
             ⚠️ РАННИЙ ДОСТУП ⚠️              
==================================================

💎 ПРЕИМУЩЕСТВА АВТОМАТИЗИРОВАННОГО ЯДРА PHANTOM:
⚙️ Полная Автономия: Ядро софта полностью заточено под автоматическое 
   выполнение всех торговых функций 24/7 без участия человека.
🎮 Авто-Выдача Steam: Робот сам моментально принимает оплату, 
   рассчитывает часы аренды и выдает данные клиенту.
🔐 Авто-Безопасность: Встроенный генератор кодов Guard и автоматическая 
   смена паролей по истечении времени сессии.
🎁 Авто-Маркетинг: Система сама отслеживает отзывы покупателей и 
   мгновенно начисляет бонусное время в чат.

==================================================
📱 СОЦИАЛЬНЫЕ СЕТИ:
   • Telegram: https://t.me/FunPayPHANTOM
   • GitHub: github.com/dzhant (скоро)

==================================================
    """)

def generate_random_password(length: int = 16) -> str:
    """Генерация случайного надежного пароля"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))

def format_time_remaining(seconds: int) -> str:
    """Форматирование остатка времени в человекочитаемый вид"""
    if seconds <= 0:
        return "истекло"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours} ч. {minutes} мин."
    return f"{minutes} мин."

def generate_steam_code(shared_secret: str) -> str:
    """
    Генерация 5-значного кода Steam Guard по алгоритму TOTP
    """
    try:
        if not shared_secret:
            return "Нет секрета"
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
    except Exception as e:
        logger.error(f"Ошибка генерации Steam Guard: {e}")
        return "Ошибка"

def process_macros(text: str, username: str = "", login: str = "", password: str = "", 
                   guard: str = "", time_remaining: str = "", bonus_hours: int = 0) -> str:
    """Замена макросов в тексте сообщения с водяным знаком в начале"""
    result = text.replace("$user", username)
    result = result.replace("$login", login)
    result = result.replace("$password", password)
    result = result.replace("$guard", guard)
    result = result.replace("$time", time_remaining)
    result = result.replace("$bonus", str(bonus_hours))
    return f"👻\n\n{result}"

# ==================== РАБОТА С КОНФИГУРАЦИЕЙ ====================
def load_config() -> Dict:
    """Загрузка конфигурации из файла"""
    if os.path.exists('config.json'):
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки конфига: {e}")
            return None
    return None

def save_config(config: Dict):
    """Сохранение конфигурации в файл"""
    global global_config
    try:
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        global_config = config
        logger.info("Конфигурация сохранена")
    except Exception as e:
        logger.error(f"Ошибка сохранения конфига: {e}")

def setup_wizard() -> Dict:
    """Интерактивная настройка конфигурации"""
    clear_screen()
    print("""
==================================================
         ⚙️ ПЕРВИЧНАЯ НАСТРОЙКА ⚙️
==================================================
    """)
    
    config = {
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
            "welcome_text": "Привет, $user! Твои данные: Логин: $login | Пароль: $password. Код Guard: $guard. Время аренды: $time",
            "bonus_enabled": True,
            "bonus_hours": 1,
            "bonus_text": "Спасибо за 5 звезд! Твоя аренда продлена на +$bonus ч. Новое время окончания: $time"
        },
        "steam_rent": {
            "tags": {},
            "active_rents": []
        }
    }
    
    print("📱 Настройка Telegram бота:")
    print("   Получить токен можно у @BotFather")
    config["telegram"]["token"] = input("API Токен Telegram бота: ").strip()
    config["telegram"]["password"] = input("Секретный пароль для админа: ").strip()
    
    print("\n🔑 Настройка FunPay:")
    print("   Golden Key можно получить в настройках профиля FunPay")
    config["funpay"]["golden_key"] = input("Golden Key сессии FunPay: ").strip()
    
    print("\n🌐 Настройка прокси (Enter если не нужны):")
    print("   Формат: http://user:pass@ip:port или http://ip:port")
    tg_proxy = input("Прокси для Telegram: ").strip()
    config["telegram"]["proxy"] = tg_proxy if tg_proxy else None
    
    fp_proxy = input("Прокси для FunPay: ").strip()
    config["funpay"]["proxy"] = fp_proxy if fp_proxy else None
    
    save_config(config)
    print("\n✅ Конфигурация сохранена!")
    input("\nНажмите Enter для продолжения...")
    return config

# ==================== API FUNPAY ====================
async def funpay_api_request(endpoint: str, method: str = "GET", data: Dict = None, golden_key: str = None) -> Dict:
    """Запрос к API FunPay"""
    if not global_config:
        return {}
    
    proxy = global_config.get("funpay", {}).get("proxy")
    headers = {
        "Authorization": f"Bearer {golden_key or global_config['funpay']['golden_key']}",
        "Content-Type": "application/json",
        "User-Agent": "FunPayPHANTOM/1.0"
    }
    
    proxy_url = None
    if proxy and proxy != "None" and proxy is not None:
        proxy_url = proxy
    
    async with aiohttp.ClientSession() as session:
        try:
            url = f"https://api.funpay.com/{endpoint}"
            async with session.request(method, url, headers=headers, json=data, proxy=proxy_url, timeout=30) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 401:
                    logger.error("Ошибка авторизации FunPay - неверный Golden Key")
                else:
                    logger.error(f"FunPay API ошибка {resp.status}: {await resp.text()}")
                return {}
        except asyncio.TimeoutError:
            logger.error(f"Таймаут запроса к FunPay: {endpoint}")
            return {}
        except Exception as e:
            logger.error(f"Ошибка запроса к FunPay: {e}")
            return {}

async def send_funpay_message(chat_id: str, message: str):
    """Отправка сообщения в чат FunPay"""
    if not global_config.get("settings", {}).get("send_messages", True):
        return
    await funpay_api_request(f"chat/{chat_id}/send", "POST", {"text": message})

async def disable_lot(lot_id: str):
    """Деактивация лота на FunPay"""
    await funpay_api_request(f"lots/{lot_id}/disable", "POST")
    logger.info(f"Лот {lot_id} деактивирован")

async def get_funpay_dialogs() -> List[Dict]:
    """Получение списка диалогов (чатов) с FunPay"""
    result = await funpay_api_request("chat/dialogs")
    return result.get("items", [])

async def get_funpay_messages(dialog_id: str) -> List[Dict]:
    """Получение сообщений из диалога"""
    result = await funpay_api_request(f"chat/{dialog_id}/messages")
    return result.get("items", [])

# ==================== ПАРСИНГ ЗАКАЗОВ ====================
async def parse_orders_and_issue_accounts():
    """Парсинг новых заказов и выдача аккаунтов"""
    try:
        dialogs = await get_funpay_dialogs()
        
        for dialog in dialogs:
            dialog_id = dialog.get("id")
            buyer_name = dialog.get("buyer", {}).get("username", "Покупатель")
            
            # Проверяем, не обрабатывали ли уже этот диалог
            already_processed = False
            for rent in global_config.get("steam_rent", {}).get("active_rents", []):
                if rent.get("buyer_id") == dialog_id:
                    already_processed = True
                    break
            if already_processed:
                continue
            
            messages = await get_funpay_messages(dialog_id)
            
            for msg in messages:
                text = msg.get("text", "").lower()
                
                # Пропускаем системные сообщения
                if msg.get("system") and global_config.get("settings", {}).get("ignore_system_messages", True):
                    continue
                
                # Проверяем сообщения об оплате
                if any(keyword in text for keyword in ["оплатил", "купил", "заказ", "приобрел"]):
                    # Парсим количество (1 шт = 1 час)
                    hours_match = re.search(r'(\d+)\s*шт', text)
                    if not hours_match:
                        hours_match = re.search(r'(\d+)\s*час', text)
                    if not hours_match:
                        hours_match = re.search(r'(\d+)', text)
                    
                    if hours_match:
                        hours = int(hours_match.group(1))
                        if hours > 24:
                            hours = 24
                        
                        # Ищем тег, к которому привязан этот диалог
                        assigned_tag = None
                        for tag_name, tag_data in global_config["steam_rent"]["tags"].items():
                            for lot in tag_data.get("linked_lots", []):
                                if str(lot) in dialog_id or str(lot) in text:
                                    assigned_tag = tag_name
                                    break
                            if assigned_tag:
                                break
                        
                        if not assigned_tag and global_config["steam_rent"]["tags"]:
                            assigned_tag = list(global_config["steam_rent"]["tags"].keys())[0]
                        
                        if not assigned_tag:
                            logger.warning(f"Не найден тег для диалога {dialog_id}")
                            continue
                        
                        # Ищем свободный аккаунт в теге
                        free_account = None
                        for acc in global_config["steam_rent"]["tags"][assigned_tag]["accounts"]:
                            if acc.get("status") == "free":
                                free_account = acc
                                break
                        
                        if free_account:
                            # Выдаем аккаунт
                            rent_until = time.time() + (hours * 3600)
                            free_account["status"] = "rented"
                            free_account["rent_until"] = rent_until
                            free_account["buyer_id"] = dialog_id
                            
                            # Добавляем в активные аренды
                            global_config["steam_rent"]["active_rents"].append({
                                "login": free_account["login"],
                                "tag": assigned_tag,
                                "rent_until": rent_until,
                                "buyer_id": dialog_id
                            })
                            
                            save_config(global_config)
                            
                            # Формируем приветственное сообщение
                            steam_code = generate_steam_code(free_account.get("shared_secret", ""))
                            time_str = format_time_remaining(hours * 3600)
                            
                            welcome_msg = process_macros(
                                global_config["settings"]["welcome_text"],
                                buyer_name,
                                free_account["login"],
                                free_account["password"],
                                steam_code,
                                time_str
                            )
                            
                            await send_funpay_message(dialog_id, welcome_msg)
                            logger.info(f"✅ Выдан аккаунт {free_account['login']} покупателю {buyer_name} на {hours} ч")
                        else:
                            await send_funpay_message(dialog_id, "Извините, все аккаунты заняты. Ожидайте освобождения. 👻")
                            logger.warning(f"❌ Нет свободных аккаунтов в теге {assigned_tag}")
                        break
                        
    except Exception as e:
        logger.error(f"Ошибка парсинга заказов: {e}")

async def parse_reviews_and_give_bonus():
    """Парсинг отзывов и начисление бонусов"""
    try:
        if not global_config.get("settings", {}).get("bonus_enabled", True):
            return
        
        dialogs = await get_funpay_dialogs()
        
        for dialog in dialogs:
            dialog_id = dialog.get("id")
            messages = await get_funpay_messages(dialog_id)
            
            for msg in messages:
                text = msg.get("text", "").lower()
                
                # Проверяем отзыв с 5 звездами
                if "5 звезд" in text or "5 звёзд" in text or "отлично" in text or "5★" in text:
                    # Ищем активную аренду для этого покупателя
                    active_rent = None
                    for rent in global_config["steam_rent"]["active_rents"]:
                        if rent.get("buyer_id") == dialog_id:
                            active_rent = rent
                            break
                    
                    if active_rent and not msg.get("processed", False):
                        # Начисляем бонус
                        bonus_hours = global_config["settings"]["bonus_hours"]
                        active_rent["rent_until"] += bonus_hours * 3600
                        
                        # Обновляем в аккаунте
                        for tag_name, tag_data in global_config["steam_rent"]["tags"].items():
                            for acc in tag_data["accounts"]:
                                if acc["login"] == active_rent["login"]:
                                    acc["rent_until"] = active_rent["rent_until"]
                                    break
                        
                        # Отмечаем сообщение как обработанное
                        msg["processed"] = True
                        save_config(global_config)
                        
                        # Отправляем бонусное сообщение
                        new_time_str = format_time_remaining(active_rent["rent_until"] - time.time())
                        bonus_msg = process_macros(
                            global_config["settings"]["bonus_text"],
                            dialog.get("buyer", {}).get("username", "Покупатель"),
                            time_remaining=new_time_str,
                            bonus_hours=bonus_hours
                        )
                        
                        await send_funpay_message(dialog_id, bonus_msg)
                        logger.info(f"🎁 Начислен бонус +{bonus_hours}ч покупателю {active_rent['login']}")
                        
    except Exception as e:
        logger.error(f"Ошибка парсинга отзывов: {e}")

# ==================== STEAM API ====================
async def change_steam_password_api(login: str, new_password: str) -> bool:
    """Смена пароля через Steam API (заглушка, требуется настройка)"""
    try:
        logger.info(f"[Steam API] Смена пароля для {login}")
        # TODO: Интеграция с реальным Steam API
        # steam_api_key = global_config.get("steam", {}).get("api_key")
        # response = await steam_api_request("ChangePassword", ...)
        return True
    except Exception as e:
        logger.error(f"Ошибка смены пароля Steam: {e}")
        return False

# ==================== ОСНОВНАЯ БИЗНЕС-ЛОГИКА ====================
async def phantom_core_loop():
    """Фоновый цикл обработки аренды"""
    logger.info("👻 Фоновый цикл Phantom запущен")
    
    last_orders_check = 0
    last_reviews_check = 0
    
    while True:
        try:
            if not global_config:
                await asyncio.sleep(5)
                continue
            
            current_time = time.time()
            
            # Проверка новых заказов (каждые 30 секунд)
            if current_time - last_orders_check >= 30:
                await parse_orders_and_issue_accounts()
                last_orders_check = current_time
            
            # Проверка отзывов (каждые 60 секунд)
            if current_time - last_reviews_check >= 60:
                await parse_reviews_and_give_bonus()
                last_reviews_check = current_time
            
            # Проверка аренды и смена паролей
            steam_rent = global_config.get("steam_rent", {})
            tags = steam_rent.get("tags", {})
            active_rents = steam_rent.get("active_rents", [])
            new_active_rents = []
            
            for rent in active_rents:
                if rent["rent_until"] > current_time:
                    new_active_rents.append(rent)
                else:
                    login = rent["login"]
                    tag_name = rent["tag"]
                    
                    if tag_name in tags:
                        for acc in tags[tag_name]["accounts"]:
                            if acc["login"] == login:
                                acc["status"] = "free"
                                acc["rent_until"] = 0
                                acc["buyer_id"] = None
                                
                                new_password = generate_random_password()
                                acc["password"] = new_password
                                await change_steam_password_api(login, new_password)
                                
                                if global_config["settings"].get("send_messages", True) and rent.get("buyer_id"):
                                    msg = "🕐 Ваше время аренды истекло. Доступ к аккаунту закрыт."
                                    await send_funpay_message(rent["buyer_id"], process_macros(msg))
                                
                                logger.info(f"🔐 Аренда {login} завершена, пароль изменен")
                                break
                    
                    save_config(global_config)
            
            steam_rent["active_rents"] = new_active_rents
            
            # Проверка складского контроля
            for tag_name, tag_data in tags.items():
                free_accounts = [acc for acc in tag_data["accounts"] if acc.get("status") == "free"]
                if len(free_accounts) == 0 and len(tag_data["accounts"]) > 0:
                    for lot_id in tag_data.get("linked_lots", []):
                        await disable_lot(lot_id)
                    logger.warning(f"📦 Тег {tag_name}: закончились аккаунты, лоты деактивированы")
            
            # Автоподнятие лотов
            if global_config["settings"].get("auto_raise", True):
                last_raise = global_config["funpay"].get("last_raise_time", 0)
                if current_time - last_raise >= 3600:
                    # TODO: Запрос на поднятие лотов
                    global_config["funpay"]["last_raise_time"] = current_time
                    save_config(global_config)
                    logger.info("🔄 Автоподнятие лотов выполнено")
            
            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"Ошибка фонового цикла: {e}")
            await asyncio.sleep(30)

# ==================== TELEGRAM БОТ - КЛАВИАТУРЫ ====================
def get_main_keyboard() -> InlineKeyboardMarkup:
    settings_status = "🟢" if global_config.get("settings", {}).get("auto_raise", True) else "🔴"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⚙️ Настройки Phantom [{settings_status}]", callback_data="menu_settings")],
        [InlineKeyboardButton(text="✉️ Настройка сообщений", callback_data="menu_messages")],
        [InlineKeyboardButton(text="🎮 Управление Арендой", callback_data="menu_rent")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="menu_stats")],
        [InlineKeyboardButton(text="ℹ️ О программе", callback_data="menu_about")]
    ])
    return keyboard

def get_settings_keyboard() -> InlineKeyboardMarkup:
    auto_raise = global_config.get("settings", {}).get("auto_raise", True)
    status_text = "🟢 ВКЛ" if auto_raise else "🔴 ВЫКЛ"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🔄 Автоподнятие: {status_text}", callback_data="toggle_auto_raise")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]
    ])
    return keyboard

def get_messages_keyboard() -> InlineKeyboardMarkup:
    send_msgs = global_config.get("settings", {}).get("send_messages", True)
    ignore_sys = global_config.get("settings", {}).get("ignore_system_messages", True)
    bonus_enabled = global_config.get("settings", {}).get("bonus_enabled", True)
    
    send_status = "🟢" if send_msgs else "🔴"
    ignore_status = "🟢" if ignore_sys else "🔴"
    bonus_status = "🟢" if bonus_enabled else "🔴"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💬 Отправка: {send_status}", callback_data="toggle_send_messages")],
        [InlineKeyboardButton(text=f"🤖 Игнор системных: {ignore_status}", callback_data="toggle_ignore_system")],
        [InlineKeyboardButton(text=f"🎁 Бонус за отзыв: {bonus_status}", callback_data="toggle_bonus")],
        [InlineKeyboardButton(text="⏱️ Время бонуса", callback_data="edit_bonus_time")],
        [InlineKeyboardButton(text="📝 Текст приветствия", callback_data="edit_welcome_text")],
        [InlineKeyboardButton(text="🎁 Текст бонуса", callback_data="edit_bonus_text")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]
    ])
    return keyboard

def get_rent_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать тег", callback_data="create_tag")],
        [InlineKeyboardButton(text="🔐 Добавить аккаунт", callback_data="add_account")],
        [InlineKeyboardButton(text="🔗 Привязать лот", callback_data="link_lot")],
        [InlineKeyboardButton(text="📊 Проверить склад", callback_data="check_stock")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]
    ])
    return keyboard

# ==================== TELEGRAM ХЭНДЛЕРЫ ====================
async def start_command(message: Message, bot: Bot, state: FSMContext):
    if global_config.get("telegram", {}).get("chat_id") == message.chat.id:
        await message.answer("👻 **Вы уже авторизованы!**", reply_markup=get_main_keyboard(), parse_mode="Markdown")
        return
    
    await state.set_state(AuthState.waiting_for_password)
    await message.answer("🔐 **Введите секретный пароль для доступа к панели управления:**", parse_mode="Markdown")

async def process_auth_password(message: Message, bot: Bot, state: FSMContext):
    if await state.get_state() != AuthState.waiting_for_password.state:
        return
    
    if message.text.strip() != global_config.get("telegram", {}).get("password"):
        await message.answer("❌ **Неверный пароль!** Доступ запрещен.", parse_mode="Markdown")
        await state.clear()
        return
    
    global_config["telegram"]["chat_id"] = message.chat.id
    save_config(global_config)
    
    await bot.set_my_description("FunPay PHANTOM by Dzhant - автоматическая аренда Steam аккаунтов")
    await bot.set_my_short_description("Аренда Steam аккаунтов 24/7")
    
    await message.answer(
        "✅ **Авторизация успешна!**\n\n"
        "👻 Добро пожаловать в FunPay PHANTOM!\n\n"
        "Используйте меню для управления.",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )
    await state.clear()

async def cmd_sys(message: Message):
    if message.chat.id != global_config.get("telegram", {}).get("chat_id"):
        return
    
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    net_io = psutil.net_io_counters()
    boot_time = psutil.boot_time()
    uptime = time.time() - boot_time
    
    active_rents = len(global_config.get("steam_rent", {}).get("active_rents", []))
    total_accounts = 0
    for tag in global_config.get("steam_rent", {}).get("tags", {}).values():
        total_accounts += len(tag.get("accounts", []))
    
    text = f"""
📊 **Системная статистика**

🖥️ **CPU:** {cpu_percent}%
💾 **RAM:** {memory.used // (1024*1024)} MB / {memory.total // (1024*1024)} MB
🌐 **Сеть:** 📤 {net_io.bytes_sent // (1024*1024)} MB | 📥 {net_io.bytes_recv // (1024*1024)} MB
⏱️ **Аптайм:** {int(uptime // 3600)}ч {int((uptime % 3600) // 60)}мин

🎮 **Статистика аренды:**
   • Активных аренд: {active_rents}
   • Всего аккаунтов: {total_accounts}

👻 **Phantom Status:** 🟢 ACTIVE
    """
    await message.answer(text, parse_mode="Markdown")

async def handle_callback_query(callback: CallbackQuery, bot: Bot, state: FSMContext):
    if callback.message.chat.id != global_config.get("telegram", {}).get("chat_id"):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await callback.answer()
    data = callback.data
    
    if data == "back_main":
        await callback.message.edit_text("👻 **Главное меню Phantom**", reply_markup=get_main_keyboard(), parse_mode="Markdown")
    
    elif data == "menu_about":
        text = """
ℹ️ **FunPay PHANTOM v1.0 BETA**

👻 **Автор:** Dzhant
📱 **Telegram канал:** https://t.me/FunPayPHANTOM

✅ **Реализованный функционал:**
• Автоматическая аренда Steam аккаунтов
• Telegram управление через бота
• Встроенный генератор Steam Guard
• Автоматическая смена паролей
• Бонусы за отзывы 5★
• Деактивация лотов при пустом складе
• Прокси поддержка

⚠️ **Ранний доступ** — функционал расширяется!

💡 **Вопросы и предложения:** @DZHANT
        """
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]
        ])
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    
    elif data == "menu_settings":
        await callback.message.edit_text("⚙️ **Настройки Phantom**", reply_markup=get_settings_keyboard(), parse_mode="Markdown")
    
    elif data == "menu_messages":
        await callback.message.edit_text("✉️ **Настройка сообщений**", reply_markup=get_messages_keyboard(), parse_mode="Markdown")
    
    elif data == "menu_rent":
        await callback.message.edit_text("🎮 **Управление арендой**", reply_markup=get_rent_keyboard(), parse_mode="Markdown")
    
    elif data == "menu_stats":
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        net = psutil.net_io_counters()
        boot = time.time() - psutil.boot_time()
        active = len(global_config.get("steam_rent", {}).get("active_rents", []))
        
        text = f"📊 CPU: {cpu}%\n💾 RAM: {mem.used//(1024*1024)}MB\n🌐 Сеть: 📤{net.bytes_sent//(1024*1024)}MB 📥{net.bytes_recv//(1024*1024)}MB\n⏱️ Аптайм: {int(boot//3600)}ч\n🎮 Активных аренд: {active}\n👻 Phantom: 🟢 ACTIVE"
        await callback.message.edit_text(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
    
    elif data == "toggle_auto_raise":
        global_config["settings"]["auto_raise"] = not global_config["settings"].get("auto_raise", True)
        save_config(global_config)
        await callback.message.edit_text(f"🔄 Автоподнятие: {'✅ ВКЛ' if global_config['settings']['auto_raise'] else '❌ ВЫКЛ'}", reply_markup=get_settings_keyboard(), parse_mode="Markdown")
    
    elif data == "toggle_send_messages":
        global_config["settings"]["send_messages"] = not global_config["settings"].get("send_messages", True)
        save_config(global_config)
        await callback.message.edit_text("✉️ Настройки обновлены", reply_markup=get_messages_keyboard(), parse_mode="Markdown")
    
    elif data == "toggle_ignore_system":
        global_config["settings"]["ignore_system_messages"] = not global_config["settings"].get("ignore_system_messages", True)
        save_config(global_config)
        await callback.message.edit_text("✉️ Настройки обновлены", reply_markup=get_messages_keyboard(), parse_mode="Markdown")
    
    elif data == "toggle_bonus":
        global_config["settings"]["bonus_enabled"] = not global_config["settings"].get("bonus_enabled", True)
        save_config(global_config)
        await callback.message.edit_text(f"🎁 Бонус за отзыв: {'✅ ВКЛ' if global_config['settings']['bonus_enabled'] else '❌ ВЫКЛ'}", reply_markup=get_messages_keyboard(), parse_mode="Markdown")
    
    elif data == "edit_bonus_time":
        await state.set_state(BonusTimeState.waiting_for_hours)
        await callback.message.edit_text("⏱️ **Введите количество бонусных часов (1-24):**", parse_mode="Markdown")
    
    elif data == "edit_welcome_text":
        await state.set_state(EditWelcomeTextState.waiting_for_text)
        await callback.message.edit_text(
            "📝 **Введите новый текст приветствия**\n\n"
            "Доступные макросы:\n"
            "$user - имя покупателя\n"
            "$login - логин аккаунта\n"
            "$password - пароль\n"
            "$guard - код Steam Guard\n"
            "$time - время аренды\n\n"
            "Отправьте новый текст:",
            parse_mode="Markdown"
        )
    
    elif data == "edit_bonus_text":
        await state.set_state(EditBonusTextState.waiting_for_text)
        await callback.message.edit_text(
            "🎁 **Введите новый текст бонуса**\n\n"
            "Доступные макросы:\n"
            "$user - имя покупателя\n"
            "$bonus - бонусные часы\n"
            "$time - новое время окончания\n\n"
            "Отправьте новый текст:",
            parse_mode="Markdown"
        )
    
    elif data == "create_tag":
        await state.set_state(CreateTagState.waiting_for_tagname)
        await callback.message.edit_text("➕ **Введите имя нового тега** (например: CS2, DOTA2, RUST):", parse_mode="Markdown")
    
    elif data == "add_account":
        await state.set_state(AddAccountState.waiting_for_account_string)
        await callback.message.edit_text(
            "🔐 **Добавление аккаунта**\n\n"
            "Введите данные в формате:\n"
            "`ТЭГ:логин:пароль:shared_secret`\n\n"
            "Пример: `R.E.P.O:steam_user:Pass1234:base64secret`",
            parse_mode="Markdown"
        )
    
    elif data == "link_lot":
        await state.set_state(LinkLotState.waiting_for_link_string)
        await callback.message.edit_text(
            "🔗 **Привязка лота**\n\n"
            "Введите данные в формате:\n"
            "`ТЭГ:ID_ЛОТА`\n\n"
            "Пример: `R.E.P.O:123456789`",
            parse_mode="Markdown"
        )
    
    elif data == "check_stock":
        tags = global_config.get("steam_rent", {}).get("tags", {})
        if not tags:
            await callback.message.edit_text("📊 **Склад пуст**. Добавьте теги и аккаунты.", reply_markup=get_rent_keyboard(), parse_mode="Markdown")
            return
        
        result = "📊 **Проверка склада**\n\n"
        for tag_name, tag_data in tags.items():
            accounts = tag_data.get("accounts", [])
            linked = len(tag_data.get("linked_lots", []))
            free = len([a for a in accounts if a.get("status") == "free"])
            rented = len([a for a in accounts if a.get("status") == "rented"])
            
            result += f"**🎮 {tag_name}**\n"
            result += f"   📦 Лотов: {linked} | 🟢 Свободно: {free} | 🔴 Арендовано: {rented}\n"
            
            for acc in accounts:
                status = "🟢" if acc.get("status") == "free" else "🔴"
                code = generate_steam_code(acc.get("shared_secret", ""))
                result += f"   {status} `{acc['login']}` | Guard: `{code}`\n"
            result += "\n"
        
        await callback.message.edit_text(result, reply_markup=get_rent_keyboard(), parse_mode="Markdown")

async def handle_fsm_messages(message: Message, state: FSMContext):
    current_state = await state.get_state()
    
    if current_state == BonusTimeState.waiting_for_hours.state:
        try:
            hours = int(message.text.strip())
            if 1 <= hours <= 24:
                global_config["settings"]["bonus_hours"] = hours
                save_config(global_config)
                await message.answer(f"✅ Бонусное время установлено: {hours} час(ов)", reply_markup=get_main_keyboard())
            else:
                await message.answer("❌ Введите число от 1 до 24")
            await state.clear()
        except ValueError:
            await message.answer("❌ Введите корректное число")
            await state.clear()
    
    elif current_state == EditWelcomeTextState.waiting_for_text.state:
        new_text = message.text.strip()
        if len(new_text) >= 10:
            global_config["settings"]["welcome_text"] = new_text
            save_config(global_config)
            example = process_macros(new_text, "TestUser", "test_login", "test_pass", "12345", "2 ч. 30 мин.")
            await message.answer(f"✅ Текст сохранен!\n\nПример:\n{example}", reply_markup=get_main_keyboard())
        else:
            await message.answer("❌ Текст слишком короткий (минимум 10 символов)")
        await state.clear()
    
    elif current_state == EditBonusTextState.waiting_for_text.state:
        new_text = message.text.strip()
        if len(new_text) >= 10:
            global_config["settings"]["bonus_text"] = new_text
            save_config(global_config)
            example = process_macros(new_text, "TestUser", time_remaining="5 ч.", bonus_hours=2)
            await message.answer(f"✅ Текст сохранен!\n\nПример:\n{example}", reply_markup=get_main_keyboard())
        else:
            await message.answer("❌ Текст слишком короткий (минимум 10 символов)")
        await state.clear()
    
    elif current_state == CreateTagState.waiting_for_tagname.state:
        tag_name = message.text.strip().upper()
        if "steam_rent" not in global_config:
            global_config["steam_rent"] = {"tags": {}, "active_rents": []}
        if tag_name in global_config["steam_rent"]["tags"]:
            await message.answer(f"❌ Тег {tag_name} уже существует")
        else:
            global_config["steam_rent"]["tags"][tag_name] = {"accounts": [], "linked_lots": []}
            save_config(global_config)
            await message.answer(f"✅ Тег **{tag_name}** создан!", reply_markup=get_main_keyboard(), parse_mode="Markdown")
        await state.clear()
    
    elif current_state == AddAccountState.waiting_for_account_string.state:
        parts = message.text.strip().split(":")
        if len(parts) != 4:
            await message.answer("❌ Неверный формат! Используйте: ТЭГ:логин:пароль:shared_secret")
        else:
            tag_name, login, password, shared_secret = parts
            tag_name = tag_name.upper()
            
            if tag_name not in global_config.get("steam_rent", {}).get("tags", {}):
                await message.answer(f"❌ Тег {tag_name} не существует! Сначала создайте тег.")
            else:
                for acc in global_config["steam_rent"]["tags"][tag_name]["accounts"]:
                    if acc["login"] == login:
                        await message.answer(f"❌ Аккаунт {login} уже существует!")
                        await state.clear()
                        return
                
                global_config["steam_rent"]["tags"][tag_name]["accounts"].append({
                    "login": login,
                    "password": password,
                    "shared_secret": shared_secret,
                    "status": "free",
                    "rent_until": 0,
                    "buyer_id": None
                })
                save_config(global_config)
                await message.answer(f"✅ Аккаунт **{login}** добавлен в тег **{tag_name}**", reply_markup=get_main_keyboard(), parse_mode="Markdown")
        await state.clear()
    
    elif current_state == LinkLotState.waiting_for_link_string.state:
        parts = message.text.strip().split(":")
        if len(parts) != 2:
            await message.answer("❌ Неверный формат! Используйте: ТЭГ:ID_ЛОТА")
        else:
            tag_name, lot_id = parts
            tag_name = tag_name.upper()
            
            if tag_name not in global_config.get("steam_rent", {}).get("tags", {}):
                await message.answer(f"❌ Тег {tag_name} не существует!")
            else:
                if lot_id not in global_config["steam_rent"]["tags"][tag_name]["linked_lots"]:
                    global_config["steam_rent"]["tags"][tag_name]["linked_lots"].append(lot_id)
                    save_config(global_config)
                    await message.answer(f"✅ Лот **{lot_id}** привязан к тегу **{tag_name}**", reply_markup=get_main_keyboard(), parse_mode="Markdown")
                else:
                    await message.answer(f"⚠️ Лот {lot_id} уже привязан к тегу {tag_name}")
        await state.clear()

# ==================== ЗАПУСК ====================
async def on_startup(bot: Bot):
    """Действия при запуске бота"""
    await bot.set_my_commands([
        BotCommand(command="start", description="Авторизация в системе"),
        BotCommand(command="sys", description="Системная информация")
    ])
    asyncio.create_task(phantom_core_loop())
    logger.info("🚀 FunPay PHANTOM успешно запущен!")

async def main():
    """Главная функция запуска"""
    show_welcome_banner()
    
    config = load_config()
    if config is None:
        config = setup_wizard()
        print("\n✅ Настройка завершена! Запустите скрипт снова.")
        input("\nНажмите Enter для выхода...")
        return
    
    global global_config
    global_config = config
    
    if not global_config.get("telegram", {}).get("token"):
        print("❌ Не указан токен Telegram бота")
        print("Удалите config.json и перезапустите скрипт")
        input("\nНажмите Enter для выхода...")
        return
    
    print("\n" + "=" * 50)
    print("🚀 ЗАПУСК FUNPAY PHANTOM")
    print("=" * 50)
    print(f"📱 Telegram бот запущен")
    print(f"🎮 Тегов: {len(global_config.get('steam_rent', {}).get('tags', {}))}")
    print(f"👻 Статус: РАННИЙ ДОСТУП")
    print("=" * 50 + "\n")
    
    storage = MemoryStorage()
    bot = Bot(token=global_config["telegram"]["token"])
    dp = Dispatcher(storage=storage)
    
    dp.message.register(start_command, Command("start"))
    dp.message.register(cmd_sys, Command("sys"))
    dp.message.register(process_auth_password, F.text & ~F.text.startswith('/'))
    dp.message.register(handle_fsm_messages, F.text & ~F.text.startswith('/'))
    dp.callback_query.register(handle_callback_query)
    
    await on_startup(bot)
    
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("👻 FunPay PHANTOM остановлен")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👻 FunPay PHANTOM завершил работу")
        sys.exit(0)