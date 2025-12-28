"""Утилиты и вспомогательные функции"""
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.management import call_command
import threading


def _start_ufaloft_background(interval: str, index_field: str, verbose: str, headless: str, mode: str) -> None:
    def run():
        args = ['--interval-min', str(interval), '--index-field', index_field]
        if verbose == '1':
            args.append('--verbose')
        try:
            if mode == 'requests':
                call_command('ufaloft_requests_watch', *args)
            else:
                # For interactive selenium mode we force GUI (no headless),
                # because the user is expected to login/2FA in the opened browser window.
                if mode != 'selenium' and headless == '1':
                    args.append('--headless')
                call_command('ufaloft_watch', *args)
        except Exception:
            pass

    threading.Thread(target=run, name='UfaloftWatchFromUI', daemon=True).start()


@login_required
def start_ufaloft_watch(request):
    """Запуск Selenium-наблюдателя из UI"""
    interval = request.GET.get('interval', '60')
    index_field = request.GET.get('index', 'first_name')
    verbose = request.GET.get('v', '1')
    headless = request.GET.get('headless', '')
    mode = request.GET.get('mode', '')  # selenium|requests

    _start_ufaloft_background(interval, index_field, verbose, headless, mode)
    if mode == 'requests':
        messages.success(request, 'UFALOFT запущен в фоне (requests). Нужны сохранённые cookies: выполните ufaloft_login.')
    elif mode == 'selenium':
        # noVNC is exposed on host port 7900 by default. We can't "open a window" on user's PC,
        # but user can open noVNC in their browser and login/2FA there.
        host = request.get_host().split(':')[0]
        messages.success(request, f'UFALOFT Selenium запущен. Откройте браузерное окно Chrome через noVNC: http://{host}:7900 (затем войдите/2FA).')
    else:
        messages.success(request, 'UFALOFT Selenium запущен в фоне. На сервере без GUI используйте mode=requests или headless=1.')
    return redirect('home')


@login_required
def ufaloft_ui(request):
    """One-click UX:
    - redirect user to noVNC tab to login/2FA and keep the browser open
    """
    host = request.get_host().split(':')[0]
    # open noVNC in a new tab (navbar uses target=_blank)
    return redirect(f'http://{host}:7900/?autoconnect=1&resize=scale')

