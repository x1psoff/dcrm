import json
import os
import re
import urllib3
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict

import requests
from bs4 import BeautifulSoup


DEFAULT_LOGIN_URL = 'https://lk.ufaloft.ru/index.php?module=dashboard/'
DEFAULT_DASHBOARD_URL = 'https://lk.ufaloft.ru/index.php?module=dashboard/'
COOKIES_PATH = os.path.join('media', 'ufaloft_cookies.json')


@dataclass
class DashboardItem:
    my_index: str  # e.g. "393"
    raw_title: str  # e.g. "3167ЮВ-393 Гульназ Старобалтачево"
    status_text: str  # text from dropdown cell
    link: str  # href of item link (absolute)
    workshop_price: str  # стоимость работы цеха из field-1227-td


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129 Safari/537.36',
    'Accept-Language': 'ru,ru-RU;q=0.9,en;q=0.8',
}


def _resolve_verify_param():
    """Return requests verify parameter value based on env.
    - UFALOFT_CA_BUNDLE: path to PEM file → used directly
    - UFALOFT_VERIFY_SSL: '1' (default) → True, '0' → False (and warnings disabled)
    """
    ca_bundle = os.environ.get('UFALOFT_CA_BUNDLE')
    if ca_bundle:
        return ca_bundle
    verify_flag = os.environ.get('UFALOFT_VERIFY_SSL', '1')
    if verify_flag == '0':
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        return False
    return True


def ensure_media_dir() -> None:
    os.makedirs('media', exist_ok=True)


def save_cookies(session: requests.Session, path: str = COOKIES_PATH) -> None:
    ensure_media_dir()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(session.cookies.get_dict(), f, ensure_ascii=False)


def load_cookies(session: requests.Session, path: str = COOKIES_PATH) -> bool:
    if not os.path.exists(path):
        return False
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        session.cookies.update(data)
        return True
    except Exception:
        return False


def _absolute(url: str, base: str) -> str:
    return url if url.startswith('http') else requests.compat.urljoin(base, url)


def login_with_credentials(session: requests.Session, username: str, password: str, login_url: str = DEFAULT_LOGIN_URL, otp_code: Optional[str] = None) -> None:
    # 1) GET login page
    resp = session.get(login_url, headers=HEADERS, timeout=30, verify=_resolve_verify_param())
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, 'html.parser')

    form = soup.find('form') or soup.select_one('form[action]')
    action = form.get('action') if form else None
    action_url = _absolute(action, login_url) if action else login_url

    payload = {}
    if form:
        for inp in form.find_all('input'):
            name = inp.get('name')
            if not name:
                continue
            payload[name] = inp.get('value', '')
    # guess fields
    ukey = _find_key(payload.keys(), ['username', 'user_name', 'login', 'email', 'phone']) or 'username'
    pkey = _find_key(payload.keys(), ['password', 'passwd', 'pwd']) or 'password'
    payload[ukey] = username
    payload[pkey] = password

    # 2) POST credentials
    resp2 = session.post(action_url, data=payload, headers=HEADERS, timeout=30, verify=_resolve_verify_param(), allow_redirects=True)
    resp2.raise_for_status()

    # 3) Detect OTP step if present
    if _page_requires_otp(resp2.text):
        if not otp_code:
            raise RuntimeError('Требуется 2FA код из WhatsApp. Запустите команду повторно с параметром --otp <code>.')
        _submit_otp(session, resp2.text, login_url, otp_code)


def _page_requires_otp(html: str) -> bool:
    soup = BeautifulSoup(html, 'html.parser')
    # Heuristics: look for input name contains code/otp
    return bool(soup.find('input', attrs={'name': re.compile(r'(otp|code)', re.I)}))


def _submit_otp(session: requests.Session, html: str, base_url: str, otp_code: str) -> None:
    soup = BeautifulSoup(html, 'html.parser')
    form = soup.find('form') or soup.select_one('form[action]')
    if not form:
        raise RuntimeError('Не найдено поле для ввода 2FA кода')
    action = form.get('action') or base_url
    action_url = _absolute(action, base_url)

    payload = {}
    for inp in form.find_all('input'):
        name = inp.get('name')
        if not name:
            continue
        payload[name] = inp.get('value', '')
    otp_key = _find_key(payload.keys(), ['otp', 'code', 'sms', 'whatsapp']) or 'otp'
    payload[otp_key] = otp_code

    resp = session.post(action_url, data=payload, headers=HEADERS, timeout=30, verify=_resolve_verify_param(), allow_redirects=True)
    resp.raise_for_status()


def _find_key(keys, preferred_names):
    for key in keys:
        for pref in preferred_names:
            if key.lower() == pref:
                return key
    for key in keys:
        for pref in preferred_names:
            if pref in key.lower():
                return key
    return None


def parse_dashboard(session: requests.Session, dashboard_url: str = DEFAULT_DASHBOARD_URL) -> List[DashboardItem]:
    resp = session.get(dashboard_url, headers=HEADERS, timeout=30, verify=_resolve_verify_param())
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, 'html.parser')

    rows = soup.select('tr.listing-table-tr') or []
    rows += soup.select('tr.listing-table-tr.unread-item-row')

    items: List[DashboardItem] = []
    for tr in rows:
        # Link and title
        link_el = tr.select_one('.item_heading_td .item_heading_link') or tr.select_one('.item_heading_link')
        if not link_el:
            continue
        title = link_el.get_text(strip=True)
        href = link_el.get('href', '')
        link_abs = _absolute(href, dashboard_url) if href else dashboard_url

        my_index = _extract_my_index_from_title(title)
        if not my_index:
            continue

        # Status cell
        status_td = tr.select_one('td.fieldtype_dropdown.field-1284-td') or tr.select_one('.fieldtype_dropdown.field-1284-td')
        status_text = status_td.get_text(strip=True) if status_td else ''

        # Workshop price cell (стоимость работы цеха)
        workshop_price_td = tr.select_one('td.fieldtype_formula.field-1227-td') or tr.select_one('.fieldtype_formula.field-1227-td')
        workshop_price = workshop_price_td.get_text(strip=True) if workshop_price_td else ''

        items.append(DashboardItem(my_index=my_index, raw_title=title, status_text=status_text, link=link_abs, workshop_price=workshop_price))

    return items


def _extract_my_index_from_title(title: str) -> Optional[str]:
    # Examples: "3167ЮВ-393 Гульназ Старобалтачево" -> 393
    # Handle hyphen, en dash, em dash: -, – (\u2013), — (\u2014)
    m = re.search(r'[\-\u2013\u2014]\s*(\d{1,10})\b', title)
    if m:
        return m.group(1)
    # Fallback: last number group in the string
    all_nums = re.findall(r'(\d{1,10})', title)
    return all_nums[-1] if all_nums else None


UFALOFT_TO_LOCAL_STATUS: Dict[str, str] = {
    'отрисовка': 'otrisovka',
    'ждем прибытия материала': 'zhdem_material',
    'ждём прибытия материала': 'zhdem_material',
    'ждет отгрузку материала': 'zhdem_material',
    'приехал в цех': 'priekhal_v_ceh',
    'на распиле': 'na_raspile',
    'заказ готов': 'zakaz_gotov',
    'готов': 'zakaz_gotov',
}


def map_external_status_to_local(external_text: str) -> Optional[str]:
    lower = (external_text or '').strip().lower()
    if not lower:
        return None
    if lower in UFALOFT_TO_LOCAL_STATUS:
        return UFALOFT_TO_LOCAL_STATUS[lower]
    for key, val in UFALOFT_TO_LOCAL_STATUS.items():
        if key in lower:
            return val
    return None


def sync_by_index(update_func, items: List[DashboardItem]) -> int:
    """update_func: callable like (my_index: str, mapped_status: Optional[str], raw_status: str, workshop_price: str) -> bool
    Returns number of updated records
    """
    updated = 0
    for item in items:
        mapped = map_external_status_to_local(item.status_text)
        ok = update_func(item.my_index, mapped, item.status_text, item.workshop_price)
        if ok:
            updated += 1
    return updated


