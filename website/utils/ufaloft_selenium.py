from typing import List

from selenium.webdriver.common.by import By

from .ufaloft import DashboardItem, _extract_my_index_from_title


def parse_dashboard_with_driver(driver) -> List[DashboardItem]:
    rows = []
    rows += driver.find_elements(By.CSS_SELECTOR, 'tr.listing-table-tr')
    rows += driver.find_elements(By.CSS_SELECTOR, 'tr.listing-table-tr.unread-item-row')

    items: List[DashboardItem] = []
    for tr in rows:
        try:
            link_el = tr.find_element(By.CSS_SELECTOR, '.item_heading_td .item_heading_link, .item_heading_link')
        except Exception:
            continue
        title = link_el.text.strip()
        href = link_el.get_attribute('href') or ''

        my_index = _extract_my_index_from_title(title)
        if not my_index:
            continue

        # статус
        status_text = ''
        try:
            status_td = tr.find_element(By.CSS_SELECTOR, 'td.fieldtype_dropdown.field-1284-td, .fieldtype_dropdown.field-1284-td')
            status_text = (status_td.text or '').strip()
        except Exception:
            pass

        # стоимость работы цеха
        workshop_price = ''
        try:
            workshop_price_td = tr.find_element(By.CSS_SELECTOR, 'td.fieldtype_formula.field-1227-td, .fieldtype_formula.field-1227-td')
            workshop_price = (workshop_price_td.text or '').strip()
        except Exception:
            pass

        items.append(DashboardItem(my_index=my_index, raw_title=title, status_text=status_text, link=href, workshop_price=workshop_price))

    return items


