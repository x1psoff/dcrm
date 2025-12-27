"""
Модульная структура views для лучшей организации кода
"""
from .auth import home, logout_user, register_user
from .records import (
    customer_record, delete_record, add_record, update_record,
    record_detail, update_record_status, set_margin_flags
)
from .products import (
    add_products_to_record, export_products, clear_products,
    product_detail, products_list, get_mounting_types_by_category,
    get_excel_data, save_excel_data, download_excel_file
)
from .files import add_file, delete_file, process_csv, process_csv_by_pk
from .expenses import (
    unplanned_expenses_list, add_unplanned_expense,
    edit_unplanned_expense, delete_unplanned_expense
)
from .calculations import (
    set_designer_manual_salary, set_designer_worker_manual_salary,
    set_assembler_worker_manual_salary, calculate_record_margin,
    calculate_record_total_components, calculate_record_total_expenses
)
from .analytics import analytics_dashboard
from .profiles import my_profile, profiles_list, staff_profile
from .utils import start_ufaloft_watch, ufaloft_ui
from .payments import payments_page, mark_payment_paid, mark_payment_unpaid
from .create_product import create_product
from .create_product import create_category

__all__ = [
    # Auth
    'home', 'logout_user', 'register_user',
    # Records
    'customer_record', 'delete_record', 'add_record', 'update_record',
    'record_detail', 'update_record_status', 'set_margin_flags',
    # Products
    'add_products_to_record', 'export_products', 'clear_products',
    'product_detail', 'products_list', 'get_mounting_types_by_category',
    'get_excel_data', 'save_excel_data', 'download_excel_file',
    # Files
    'add_file', 'delete_file', 'process_csv', 'process_csv_by_pk',
    # Expenses
    'unplanned_expenses_list', 'add_unplanned_expense',
    'edit_unplanned_expense', 'delete_unplanned_expense',
    # Calculations
    'set_designer_manual_salary', 'set_designer_worker_manual_salary',
    'set_assembler_worker_manual_salary', 'calculate_record_margin',
    'calculate_record_total_components', 'calculate_record_total_expenses',
    # Analytics
    'analytics_dashboard',
    # Profiles
    'my_profile', 'profiles_list', 'staff_profile',
    # Utils
    'start_ufaloft_watch', 'ufaloft_ui',
    # Payments
    'payments_page', 'mark_payment_paid', 'mark_payment_unpaid',
    # Create Product
    'create_product', 'create_category',
]

