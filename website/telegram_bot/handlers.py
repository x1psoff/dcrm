"""
Обработчики команд и сообщений для Telegram бота
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from asgiref.sync import sync_to_async
from website.models import Profile

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    welcome_message = (
        f"Привет, {user.first_name}! 👋\n\n"
        "Я бот для управления CRM системой.\n"
        "Используйте /help для просмотра доступных команд."
    )
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "📋 Доступные команды:\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n"
        "/profile - Посмотреть свой профиль\n"
        "/verify КОД - Подтвердить аккаунт (код из профиля на сайте)\n\n"
        "Для подтверждения аккаунта:\n"
        "1. Зайдите в профиль на сайте\n"
        "2. Нажмите 'Получить код'\n"
        "3. Отправьте мне команду /verify с этим кодом"
    )
    await update.message.reply_text(help_text)


@sync_to_async
def get_profile_info(telegram_id):
    """Получает информацию о профиле по Telegram ID и возвращает словарь"""
    profile = Profile.objects.filter(
        telegram_id=telegram_id
    ).select_related(
        'user',
        'designer',
        'designer__profession',
        'designer__method'
    ).first()
    
    if not profile:
        return None
    
    # Определяем тип пользователя
    if profile.user.is_superuser:
        user_type = "Администратор"
    elif profile.user.is_staff:
        user_type = "Менеджер"
    elif profile.designer:
        user_type = "Работник"
    else:
        user_type = "Заказчик"
    
    # Собираем все данные в словарь, чтобы не обращаться к БД из async контекста
    data = {
        'full_name': profile.user.get_full_name() or 'Не указано',
        'username': profile.user.username,
        'telegram_verified': profile.telegram_verified,
        'has_designer': bool(profile.designer),
        'user_type': user_type,
    }
    
    # Если есть привязанный работник, добавляем его данные
    if profile.designer:
        designer = profile.designer
        data['designer'] = {
            'name': f"{designer.name} {designer.surname}",
            'profession': designer.profession.name if designer.profession else None,
            'method': designer.method.name if designer.method else None,
            'percentage': designer.percentage,
            'rate_per_square_meter': designer.rate_per_square_meter,
        }
    
    return data


@sync_to_async
def find_profile_by_code(verification_code):
    """Находит профиль по коду верификации (синхронная функция для async)"""
    return Profile.objects.filter(
        verification_code=verification_code,
        telegram_verified=False
    ).first()


@sync_to_async
def verify_profile(profile, telegram_id):
    """Подтверждает профиль (синхронная функция для async)"""
    profile.telegram_id = telegram_id
    profile.telegram_verified = True
    profile.verification_code = None
    profile.save()
    return profile.user.get_full_name() or profile.user.username


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /profile для просмотра информации о пользователе"""
    user = update.effective_user
    telegram_id = str(user.id)
    
    try:
        # Получаем информацию о профиле
        profile_data = await get_profile_info(telegram_id)
        
        if not profile_data:
            await update.message.reply_text(
                "❌ Ваш аккаунт не подтвержден.\n\n"
                "Для подтверждения:\n"
                "1. Зайдите на сайт в раздел профиля\n"
                "2. Нажмите 'Получить код'\n"
                "3. Отправьте команду /verify с полученным кодом"
            )
            return
        
        # Формируем сообщение с информацией о профиле
        profile_info = f"👤 **Ваш профиль**\n\n"
        profile_info += f"**ФИО:** {profile_data['full_name']}\n"
        profile_info += f"**Username:** @{user.username or 'не указан'}\n"
        profile_info += f"**Telegram ID:** `{telegram_id}`\n"
        profile_info += f"**Логин в системе:** {profile_data['username']}\n"
        profile_info += f"**Тип аккаунта:** {profile_data['user_type']}\n"
        profile_info += f"**Статус:** {'✅ Подтвержден' if profile_data['telegram_verified'] else '⚠️ Не подтвержден'}\n\n"
        
        # Информация о роли (работник или обычный пользователь)
        if profile_data['has_designer']:
            designer = profile_data['designer']
            profile_info += "👔 **Роль: РАБОТНИК**\n\n"
            
            # Отображаем профессию
            if designer['profession']:
                profile_info += f"**Должность:** {designer['profession']}\n"
            
            profile_info += f"**Имя в системе:** {designer['name']}\n"
            
            # Добавляем метод расчета если есть
            if designer['method']:
                profile_info += f"**Метод расчета:** {designer['method']}\n"
            
            # Добавляем процент или ставку
            if designer['percentage']:
                profile_info += f"**Процент:** {designer['percentage']}%\n"
            if designer['rate_per_square_meter']:
                profile_info += f"**Ставка за м²:** {designer['rate_per_square_meter']} ₽\n"
        else:
            profile_info += "👥 **Роль: ОБЫЧНЫЙ ПОЛЬЗОВАТЕЛЬ**\n\n"
            profile_info += "У вас нет назначенной должности.\n"
            profile_info += "Для назначения роли работника обратитесь к администратору."
        
        await update.message.reply_text(profile_info, parse_mode='Markdown')
        logger.info(f"Пользователь {user.username} просмотрел свой профиль")
        
    except Exception as e:
        logger.error(f"Ошибка при получении профиля: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Произошла ошибка при получении информации о профиле.\n"
            "Пожалуйста, попробуйте позже."
        )


async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /verify для подтверждения аккаунта"""
    user = update.effective_user
    telegram_id = str(user.id)
    
    # Проверяем, что передан код
    if not context.args:
        await update.message.reply_text(
            "❌ Использование: /verify КОД\n\n"
            "Пример: /verify 123456\n\n"
            "Код можно получить в профиле на сайте."
        )
        return
    
    verification_code = context.args[0]
    
    try:
        # Ищем профиль с таким кодом верификации
        profile = await find_profile_by_code(verification_code)
        
        if not profile:
            await update.message.reply_text(
                "❌ Неверный код верификации или аккаунт уже подтвержден.\n\n"
                "Проверьте код в профиле на сайте или получите новый."
            )
            logger.warning(f"Неудачная попытка верификации от {user.username} с кодом {verification_code}")
            return
        
        # Подтверждаем аккаунт
        username = await verify_profile(profile, telegram_id)
        
        success_message = (
            f"✅ Аккаунт успешно подтвержден!\n\n"
            f"👤 Пользователь: {username}\n"
            f"🆔 Telegram ID: {telegram_id}\n\n"
            f"Теперь вы будете получать уведомления от системы."
        )
        await update.message.reply_text(success_message)
        logger.info(f"Успешная верификация пользователя {username} (TG: {user.username})")
        
    except Exception as e:
        logger.error(f"Ошибка при верификации: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при подтверждении аккаунта.\n"
            "Пожалуйста, попробуйте позже или обратитесь к администратору."
        )


async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_message = update.message.text
    logger.info(f"Получено сообщение от {update.effective_user.username}: {user_message}")
    
    response = f"Вы написали: {user_message}\n\nПока что я только учусь. Скоро здесь будет больше функций!"
    await update.message.reply_text(response)

