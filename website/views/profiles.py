"""Функции для работы с профилями"""
import random
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.conf import settings
from ..models import Profile, Designer, TailscaleInviteLink


def generate_verification_code():
    """Генерирует 6-значный код верификации"""
    return ''.join(random.choices(string.digits, k=6))


@login_required
def my_profile(request):
    """Страница профиля пользователя"""
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'generate_code':
            # Генерация кода верификации
            profile.verification_code = generate_verification_code()
            profile.telegram_verified = False
            profile.save()
            messages.success(
                request, 
                f'Код верификации: {profile.verification_code}. '
                f'Отправьте команду /verify {profile.verification_code} боту в Telegram.'
            )
            return redirect('my_profile')
        
        elif action == 'update_profile':
            # Обновление профиля
            user = request.user
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.save()
            
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('my_profile')
    
    return render(request, 'my_profile.html', {
        'profile': profile,
        'edit_user': request.user,
        'is_admin_edit': False,
    })


@login_required
def staff_profile(request, user_id: int):
    """Профиль любого пользователя (для staff), UI как 'Мой профиль'."""
    if not request.user.is_staff:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('home')

    edit_user = get_object_or_404(User, id=user_id)
    profile, _ = Profile.objects.get_or_create(user=edit_user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'generate_code':
            profile.verification_code = generate_verification_code()
            profile.telegram_verified = False
            profile.save()
            messages.success(
                request,
                f'Код верификации для {edit_user.username}: {profile.verification_code}. '
                f'Отправьте команду /verify {profile.verification_code} боту в Telegram.'
            )
            return redirect('staff_profile', user_id=edit_user.id)

        elif action == 'update_profile':
            edit_user.first_name = request.POST.get('first_name', '')
            edit_user.last_name = request.POST.get('last_name', '')
            edit_user.save(update_fields=['first_name', 'last_name'])
            messages.success(request, f'Профиль "{edit_user.username}" обновлен!')
            return redirect('staff_profile', user_id=edit_user.id)

    return render(request, 'my_profile.html', {
        'profile': profile,
        'edit_user': edit_user,
        'is_admin_edit': True,
    })


@login_required
def profiles_list(request):
    """Список всех профилей для управления (только для staff)"""
    if not request.user.is_staff:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('home')
    
    # Одноразовые ссылки для VPN (Tailscale). Выдаются по одной на созданный аккаунт.
    TAILSCALE_SINGLE_USE_LINKS = [
        "https://login.tailscale.com/uinv/i5Tb7okunnH6M5An86tN221",
        "https://login.tailscale.com/uinv/iatG66JWV1X5M5An86tN221",
        "https://login.tailscale.com/uinv/iSQGTJngcYB9M5An86tN221",
    ]

    # Засеиваем ссылки в БД (если их ещё нет).
    existing_urls = set(TailscaleInviteLink.objects.values_list("url", flat=True))
    missing = [TailscaleInviteLink(url=u) for u in TAILSCALE_SINGLE_USE_LINKS if u not in existing_urls]
    if missing:
        TailscaleInviteLink.objects.bulk_create(missing, ignore_conflicts=True)
    
    # Создаем профили для всех пользователей
    users = User.objects.all()
    for user in users:
        Profile.objects.get_or_create(user=user)
    
    # Получаем профили с предзагрузкой
    profiles = Profile.objects.select_related(
        'user', 
        'designer', 
        'designer__profession', 
        'designer__method'
    ).all()
    
    # Фильтрация
    filter_type = request.GET.get('type', 'all')
    search_query = request.GET.get('search', '').strip()
    
    if filter_type == 'workers':
        profiles = profiles.exclude(designer__isnull=True)
    elif filter_type == 'customers':
        profiles = profiles.filter(designer__isnull=True).exclude(user__is_staff=True)
    elif filter_type == 'admins':
        profiles = profiles.filter(user__is_staff=True)
    
    if search_query:
        from django.db.models import Q
        profiles = profiles.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(designer__name__icontains=search_query) |
            Q(designer__surname__icontains=search_query)
        )
    
    profiles = profiles.order_by('user__username')
    
    # Обработка POST запросов
    if request.method == 'POST':
        action = request.POST.get("action")

        if action == "create_account":
            # Создание аккаунта (логин/пароль). VPN выдаём только сотрудникам (staff).
            account_type = request.POST.get("account_type", "customer")
            needs_vpn = account_type == "staff"
            first_name = (request.POST.get("first_name") or "").strip()
            last_name = (request.POST.get("last_name") or "").strip()

            # Генерируем уникальный username
            username = None
            for _ in range(50):
                candidate = f"user{random.randint(100000, 999999)}"
                if not User.objects.filter(username=candidate).exists():
                    username = candidate
                    break
            if not username:
                messages.error(request, "Не удалось сгенерировать логин. Попробуйте ещё раз.")
                return redirect("profiles_list")

            password = "".join(random.choices(string.ascii_letters + string.digits, k=10))

            user = User.objects.create_user(username=username, password=password)
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            # Тип аккаунта: заказчик или менеджер (staff)
            if account_type == "staff":
                user.is_staff = True
                user.save(update_fields=["first_name", "last_name", "is_staff"])
            else:
                user.save(update_fields=["first_name", "last_name"])

            Profile.objects.get_or_create(user=user)

            site_url = settings.SITE_URL or request.build_absolute_uri("/")

            invite_url = None
            if needs_vpn:
                # Берём первую свободную ссылку и помечаем её как использованную (чтобы не выдать повторно)
                with transaction.atomic():
                    invite = (
                        TailscaleInviteLink.objects.select_for_update()
                        .filter(used_at__isnull=True)
                        .order_by("id")
                        .first()
                    )
                    if invite:
                        invite.mark_used(user=user)
                        invite_url = invite.url

            request.session["created_account_info"] = {
                "site_url": site_url,
                "username": username,
                "password": password,
                "invite_url": invite_url,
                "needs_vpn": needs_vpn,
                "account_type": account_type,
                "first_name": first_name,
                "last_name": last_name,
            }

            if not needs_vpn:
                messages.success(request, f"Аккаунт создан (заказчик): {username}.")
            else:
                if invite_url:
                    messages.success(request, f"Аккаунт создан (staff): {username}. Выдана VPN-ссылка.")
                else:
                    messages.warning(request, f"Аккаунт создан (staff): {username}. VPN-ссылок не осталось — обратитесь к администратору.")
            return redirect("profiles_list")

        profile_id = request.POST.get('profile_id')
        designer_id = request.POST.get('designer_id')
        
        if profile_id:
            profile = get_object_or_404(Profile, id=profile_id)
            if designer_id:
                designer = get_object_or_404(Designer, id=designer_id)
                profile.designer = designer
                messages.success(request, f'✓ {profile.user.username} → {designer.name} {designer.surname}')
            else:
                profile.designer = None
                messages.success(request, f'✓ Привязка удалена для {profile.user.username}')
            profile.save()
            return redirect('profiles_list')
    
    # Получаем всех дизайнеров
    designers = Designer.objects.select_related('profession', 'method').all()

    created_account_info = request.session.pop("created_account_info", None)
    tailscale_remaining = TailscaleInviteLink.objects.filter(used_at__isnull=True).count()
    
    # Статистика
    stats = {
        'total': Profile.objects.count(),
        'workers': Profile.objects.exclude(designer__isnull=True).count(),
        'customers': Profile.objects.filter(designer__isnull=True).exclude(user__is_staff=True).count(),
        'admins': Profile.objects.filter(user__is_staff=True).count(),
    }
    
    return render(request, 'profiles_list.html', {
        'profiles': profiles,
        'designers': designers,
        'stats': stats,
        'current_filter': filter_type,
        'search_query': search_query,
        'created_account_info': created_account_info,
        'tailscale_remaining': tailscale_remaining,
    })

