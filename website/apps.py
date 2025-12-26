from django.apps import AppConfig


class WebsiteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'website'

    def ready(self):
        # Импортируем сигналы для автоматического создания профилей
        try:
            import website.signals  # noqa
        except ImportError:
            pass
        
        # Стартуем планировщик, если включен через переменную окружения
        try:
            from . import apscheduler
            apscheduler.start()
        except Exception:
            # Избегаем падения при миграциях/коллектах и пр.
            pass

