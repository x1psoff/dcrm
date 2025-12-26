"""Утилиты и вспомогательные функции"""
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.management import call_command
import threading


@login_required
def start_ufaloft_watch(request):
    """Запуск Selenium-наблюдателя из UI"""
    interval = request.GET.get('interval', '60')
    index_field = request.GET.get('index', 'first_name')
    verbose = request.GET.get('v', '1')
    headless = request.GET.get('headless', '')

    def run():
        args = ['--interval-min', str(interval), '--index-field', index_field]
        if verbose == '1':
            args.append('--verbose')
        if headless == '1':
            args.append('--headless')
        try:
            call_command('ufaloft_watch', *args)
        except Exception:
            pass

    threading.Thread(target=run, name='UfaloftWatchFromUI', daemon=True).start()
    messages.success(request, 'Наблюдатель UFALOFT запущен в фоне')
    return redirect('home')

