import re
import time
from decimal import Decimal
from typing import Optional, Tuple

import requests
from bs4 import BeautifulSoup

from django.utils import timezone
from .models import Product, Category


def _ensure_category() -> Category:
    category, _ = Category.objects.get_or_create(name='Петли', defaults={"parent": None})
    return category


def _detect_mounting_type(text: str) -> str:
    lower = text.lower()
    if 'полунаклад' in lower:
        return 'полунакладная'
    if 'вкладн' in lower:
        return 'вкладная'
    if 'накладн' in lower:
        return 'накладная'
    if 'фальш' in lower or 'фальш-план' in lower or 'под фальш' in lower:
        return 'фальш-планка'
    return ''


def _detect_closing_type(text: str) -> str:
    lower = text.lower()
    if 'silent system' in lower or 'доводч' in lower or 'демпфер' in lower:
        return 'с доводчиком'
    if 'без довод' in lower or 'без демпф' in lower:
        return 'без доводчика'
    if 'без пруж' in lower:
        return 'без пружинки'
    return ''


def _extract_price_rub(text: str) -> Optional[Decimal]:
    t = text.replace('\xa0', ' ').replace(' ', '').replace(',', '.')
    m = re.search(r'(\d{2,}(?:[\.]\d{1,2})?)\s*руб\.?', t, flags=re.IGNORECASE)
    if m:
        try:
            return Decimal(m.group(1))
        except Exception:
            return None
    m2 = re.search(r'(\d{3,})', t)
    if m2:
        try:
            return Decimal(m2.group(1))
        except Exception:
            return None
    return None


def parse_amix_category_hinges(base_url: str, start_page: int = 1, end_page: int = 1, delay_sec: float = 0.6) -> int:
    """Парсит только петли из контейнера .category-content (и похожих) на страницах с параметром ?p=.
    В название сохраняется исходный заголовок карточки; фильтруются только названия, содержащие "петл".
    """
    category = _ensure_category()

    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129 Safari/537.36',
        'Accept-Language': 'ru,en;q=0.8',
    }

    changed_total = 0

    for page in range(start_page, end_page + 1):
        url = f"{base_url}?p={page}"
        resp = session.get(url, headers=headers, timeout=20, verify=False)
        if resp.status_code != 200:
            break

        soup = BeautifulSoup(resp.content, 'html.parser')
        container = (
            soup.select_one('.category-content')
            or soup.select_one('.catalog-content')
            or soup.select_one('.category__content')
            or soup.select_one('.catalog__content')
            or soup.select_one('[class*="category"][class*="content"]')
            or soup.select_one('[class*="catalog"][class*="content"]')
        )
        if not container:
            break

        cards = []
        for a in container.find_all('a', href=True):
            href = a['href']
            title = ' '.join(a.get_text(strip=True).split())
            if not href or not title:
                continue
            if 'петл' not in title.lower():
                continue
            if 'демпфер' in title.lower() or 'регулятор' in title.lower():
                continue
            card = a.find_parent('div') or container
            price_text = card.get_text(separator=' ', strip=True) if card else ''
            cards.append((href, title, price_text))

        seen = set()
        unique = []
        for href, title, ptxt in cards:
            key = (href, title)
            if key in seen:
                continue
            seen.add(key)
            unique.append((href, title, ptxt))

        if not unique:
            break

        for href, title, price_txt in unique:
            source_url = href if href.startswith('http') else ('https://amix-tk.ru' + href)
            mounting_type = _detect_mounting_type(title)
            closing_type = _detect_closing_type(title)
            price = _extract_price_rub(price_txt) or Decimal('0')

            product, created = Product.objects.get_or_create(
                name=title,
                category=category,
                defaults={
                    'mounting_type': mounting_type,
                    'hinge_closing_type': closing_type,
                    'our_price': price,
                    'source_url': source_url,
                    'last_parsed': timezone.now(),
                }
            )

            changed = False
            if mounting_type and product.mounting_type != mounting_type:
                product.mounting_type = mounting_type
                changed = True
            if closing_type and product.hinge_closing_type != closing_type:
                product.hinge_closing_type = closing_type
                changed = True
            if price and product.our_price != price:
                product.our_price = price
                changed = True
            if source_url and product.source_url != source_url:
                product.source_url = source_url
                changed = True

            if changed:
                product.last_parsed = timezone.now()
                product.save()
                changed_total += 1
            else:
                changed_total += 1 if created else 0

        time.sleep(delay_sec)

    return changed_total


def parse_amix_detail_page(url: str) -> dict:
    """Парсит detail-страницу AMIX: name (.detail-info-heading), closing type, angle из .detail-info-box, mounting type из названия."""
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129 Safari/537.36',
        'Accept-Language': 'ru,en;q=0.8',
    }
    resp = session.get(url, headers=headers, timeout=20, verify=False)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, 'html.parser')

    heading_el = soup.select_one('.detail-info-heading')
    name = heading_el.get_text(strip=True) if heading_el else ''

    box = soup.select_one('.detail-info-box') or soup
    closing_type = ''
    angle = ''
    for span in box.find_all('span'):
        label = span.get_text(strip=True).lower()
        if 'тип открывания/закрывания' in label:
            em = span.find_next('em')
            if em:
                closing_type = em.get_text(strip=True)
        if 'угол открывания' in label:
            em = span.find_next('em')
            if em:
                m = re.search(r'(\d{2,3})', em.get_text(strip=True))
                angle = m.group(1) if m else ''

    # Извлекаем тип петли из названия
    mounting_type = _detect_mounting_type(name)

    return {'name': name, 'hinge_closing_type': closing_type, 'hinge_angle': angle, 'mounting_type': mounting_type}


def parse_links_file_and_save(file_path: str = 'parse_links.txt') -> int:
    """Читает ссылки из файла и сохраняет товары: полное имя из heading, тип закрывания и угол из info-box."""
    category = _ensure_category()
    changed = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            links = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    except Exception:
        links = []

    for url in links:
        data = parse_amix_detail_page(url)
        name = data.get('name') or url
        closing = data.get('hinge_closing_type', '')
        angle = data.get('hinge_angle', '')
        mounting_type = data.get('mounting_type', '')
        if 'петл' not in name.lower():
            # фильтруем не-петли
            continue

        product, created = Product.objects.get_or_create(
            source_url=url,
            defaults={
                'name': name,
                'category': category,
                'hinge_closing_type': closing,
                'hinge_angle': angle,
                'mounting_type': mounting_type,
                'our_price': Decimal('0'),
                'last_parsed': timezone.now(),
            }
        )

        to_save = False
        if product.name != name:
            product.name = name
            to_save = True
        if closing and product.hinge_closing_type != closing:
            product.hinge_closing_type = closing
            to_save = True
        if angle and product.hinge_angle != angle:
            product.hinge_angle = angle
            to_save = True
        if mounting_type and product.mounting_type != mounting_type:
            product.mounting_type = mounting_type
            to_save = True
        if product.category_id != category.id:
            product.category = category
            to_save = True

        if to_save:
            product.last_parsed = timezone.now()
            product.save()
            changed += 1
        else:
            changed += 1 if created else 0

        time.sleep(0.2)

    return changed


