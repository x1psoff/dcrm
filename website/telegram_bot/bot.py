"""
Основной модуль Telegram бота
"""
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from django.conf import settings
import django

# Загружаем переменные окружения из .env файла
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / '.env')

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dcrm.settings')
django.setup()

from .handlers import (
    start_command,
    help_command,
    profile_command,
    verify_command,
    echo_message,
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Hide sensitive data: third-party libs may log full URLs (including bot token) at INFO/DEBUG.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.INFO)
logging.getLogger("telegram.ext").setLevel(logging.INFO)


def create_bot():
    """Создает и настраивает экземпляр бота"""
    # Пробуем получить токен из переменных окружения или из Django settings
    token = os.environ.get('TELEGRAM_BOT_TOKEN') or getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if not token:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN не установлен!\n"
            "Добавьте токен в файл .env:\n"
            "TELEGRAM_BOT_TOKEN=ваш_токен_здесь"
        )
    
    application = Application.builder().token(token).build()
    
    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("verify", verify_command))
    
    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message))
    
    return application


def run_bot():
    """Запускает бота"""
    application = create_bot()
    logger.info("Бот запущен и готов к работе")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

