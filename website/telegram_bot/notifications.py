"""
Модуль для отправки уведомлений в Telegram
"""
import logging
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from django.conf import settings
import os

logger = logging.getLogger(__name__)


def send_telegram_notification(telegram_id: str, message: str):
    """
    Отправляет уведомление в Telegram синхронно
    
    Args:
        telegram_id: ID пользователя в Telegram
        message: Текст сообщения
    """
    token = os.environ.get('TELEGRAM_BOT_TOKEN') or getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не настроен")
        return False
    
    if not telegram_id:
        logger.warning("telegram_id не указан")
        return False
    
    try:
        # Создаем новый event loop для синхронного вызова из Django
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def send_message():
            bot = Bot(token=token)
            await bot.send_message(chat_id=telegram_id, text=message, parse_mode='Markdown')
        
        loop.run_until_complete(send_message())
        loop.close()
        
        logger.info(f"Уведомление отправлено в Telegram: {telegram_id}")
        return True
        
    except TelegramError as e:
        logger.error(f"Ошибка отправки в Telegram: {e}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка при отправке в Telegram: {e}")
        return False


def notify_workers_about_record(record, message_type='created'):
    """
    Отправляет уведомление всем работникам, связанным с заказом
    
    Args:
        record: объект Record
        message_type: тип уведомления ('created', 'status_changed')
    """
    from website.models import Profile
    
    logger.info(f"notify_workers_about_record вызвана для заказа #{record.id}, тип: {message_type}")
    
    # Собираем всех работников
    workers = []
    
    if record.designer:
        workers.append(('Проектировщик', record.designer))
        logger.info(f"Добавлен Проектировщик: {record.designer.name} {record.designer.surname}")
    if record.designer_worker:
        workers.append(('Дизайнер', record.designer_worker))
        logger.info(f"Добавлен Дизайнер: {record.designer_worker.name} {record.designer_worker.surname}")
    if record.assembler_worker:
        workers.append(('Сборщик', record.assembler_worker))
        logger.info(f"Добавлен Сборщик: {record.assembler_worker.name} {record.assembler_worker.surname}")
    
    if not workers:
        logger.warning(f"Нет назначенных работников для заказа #{record.id}")
        return
    
    # Формируем сообщение
    status_display = dict(record.STATUS_CHOICES).get(record.status, record.status)
    
    if message_type == 'created':
        message_template = (
            "🆕 **Новый заказ №{id}**\n\n"
            "👤 Клиент: {client}\n"
            "📍 Адрес: {address}\n"
            "📊 Статус: {status}\n"
            "💰 Сумма: {amount} ₽\n\n"
            "Вы назначены: **{role}**"
        )
    else:  # status_changed
        message_template = (
            "🔄 **Изменен статус заказа №{id}**\n\n"
            "👤 Клиент: {client}\n"
            "📊 Новый статус: **{status}**\n"
            "💰 Сумма: {amount} ₽\n\n"
            "Ваша роль: **{role}**"
        )
    
    # Отправляем уведомления каждому работнику
    for role, worker in workers:
        try:
            logger.info(f"Поиск профиля для работника {worker.name} {worker.surname} (ID: {worker.id})")
            
            # Получаем профиль работника
            profile = Profile.objects.filter(
                designer=worker,
                telegram_verified=True,
                telegram_id__isnull=False
            ).first()
            
            if profile and profile.telegram_id:
                logger.info(f"Профиль найден: user={profile.user.username}, telegram_id={profile.telegram_id}")
                
                message = message_template.format(
                    id=record.id,
                    client=f"{record.first_name} {record.last_name}",
                    address=record.address or 'Не указан',
                    status=status_display,
                    amount=record.contract_amount or 0,
                    role=role
                )
                
                logger.info(f"Отправка сообщения работнику {worker.name} {worker.surname}")
                result = send_telegram_notification(profile.telegram_id, message)
                
                if result:
                    logger.info(f"✓ Уведомление успешно отправлено работнику {worker.name} {worker.surname} ({role})")
                else:
                    logger.error(f"✗ Не удалось отправить уведомление работнику {worker.name} {worker.surname}")
            else:
                if not profile:
                    logger.warning(f"Профиль не найден для работника {worker.name} {worker.surname}")
                elif not profile.telegram_verified:
                    logger.warning(f"У работника {worker.name} {worker.surname} Telegram не подтвержден")
                elif not profile.telegram_id:
                    logger.warning(f"У работника {worker.name} {worker.surname} нет telegram_id")
                
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления работнику {worker}: {e}", exc_info=True)


def notify_worker_payment_paid(payment) -> bool:
    """
    Отправляет работнику уведомление о том, что его выплата по заказу отмечена как оплаченная.

    Сообщение содержит:
    - номер заказа / клиент
    - роль
    - начислено (gross)
    - санкционные вычеты (с причинами)
    - к выплате (net)
    - краткое описание расчёта (процент/погонный/м²)
    """
    from decimal import Decimal
    from website.models import Profile

    if not payment:
        return False

    record = getattr(payment, "record", None)
    worker = getattr(payment, "worker", None)
    if not record or not worker:
        return False

    profile = Profile.objects.filter(
        designer=worker,
        telegram_verified=True,
        telegram_id__isnull=False,
    ).first()
    if not (profile and profile.telegram_id):
        logger.warning(
            f"[tg] worker payment notify skipped: no verified telegram for worker={getattr(worker, 'id', None)}"
        )
        return False

    # Deductions
    deductions_qs = getattr(payment, "deductions", None)
    deductions = list(deductions_qs.all()) if deductions_qs is not None else []
    deductions_total = sum((d.amount for d in deductions), Decimal("0"))
    gross = payment.amount or Decimal("0")
    net = gross - deductions_total

    # Basis (simplified, matches logic in payments)
    method_name = (worker.method.name.lower() if getattr(worker, "method", None) else "").strip()
    basis_text = "—"
    try:
        if ("процент" in method_name) and getattr(worker, "percentage", None) and getattr(record, "contract_amount", None):
            basis_text = f"{worker.percentage}% от договора ({record.contract_amount} ₽)"
        elif "погон" in method_name:
            rate = Decimal(str(worker.rate_per_square_meter)) if getattr(worker, "rate_per_square_meter", None) else Decimal("0")
            meters = Decimal("0")
            if payment.role == "designer":
                meters = Decimal(str(record.designer_manual_salary)) if record.designer_manual_salary is not None else Decimal("0")
            elif payment.role == "designer_worker":
                meters = Decimal(str(record.designer_worker_manual_salary)) if record.designer_worker_manual_salary is not None else Decimal("0")
            elif payment.role == "assembler_worker":
                meters = Decimal(str(record.assembler_worker_manual_salary)) if record.assembler_worker_manual_salary is not None else Decimal("0")
            basis_text = f"{meters} м × {rate} ₽/м"
        elif ("м²" in method_name or "метр" in method_name) and getattr(worker, "rate_per_square_meter", None):
            # area is optional (depends on uploaded files); avoid heavy IO here
            rate = Decimal(str(worker.rate_per_square_meter)) if worker.rate_per_square_meter else Decimal("0")
            basis_text = f"м² × {rate} ₽/м²"
    except Exception:
        basis_text = "—"

    role_display = payment.get_role_display() if hasattr(payment, "get_role_display") else str(payment.role)
    client = f"{record.first_name} {record.last_name}".strip()

    lines = [
        "✅ **Выплата оплачена**",
        "",
        f"🧾 Заказ №{record.id} — {client}",
        f"👔 Роль: **{role_display}**",
        f"💵 Начислено: **{gross:.2f} ₽**",
    ]
    if deductions_total > 0:
        lines.append(f"⚠️ Вычеты: **{deductions_total:.2f} ₽**")
    lines.append(f"✅ К выплате: **{net:.2f} ₽**")
    lines.append(f"📐 Расчет: {basis_text}")

    if deductions_total > 0:
        lines.append("")
        lines.append("🧾 Причины вычетов:")
        for d in deductions[:20]:
            reason = (d.reason or "").strip() or "—"
            lines.append(f"- {d.amount:.2f} ₽ — {reason}")
        if len(deductions) > 20:
            lines.append(f"... и еще {len(deductions) - 20}")

    message = "\n".join(lines)
    return send_telegram_notification(profile.telegram_id, message)

