from django.urls import path

from website.views import create_product, products_list
from website.views.customer_profile import customer_detail
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('record/<int:pk>/excel-data/', get_excel_data, name='get_excel_data'),
    path('record/<int:pk>/save-excel/', save_excel_data, name='save_excel_data'),
    path('record/<int:pk>/download-excel/', download_excel_file, name='download_excel_file'),
    path('record/<int:pk>/add-expense/', add_unplanned_expense, name='add_unplanned_expense'),
    path('unplanned-expenses/delete/<int:pk>/', delete_unplanned_expense, name='delete_unplanned_expense'),
    path('record/<int:pk>/', record_detail, name='record_detail'),
    path('record/<int:pk>/designer-manual/', set_designer_manual_salary, name='set_designer_manual_salary'),
    path('record/<int:pk>/designer-worker-manual/', set_designer_worker_manual_salary, name='set_designer_worker_manual_salary'),
    path('record/<int:pk>/assembler-worker-manual/', set_assembler_worker_manual_salary, name='set_assembler_worker_manual_salary'),
    path('record/<int:pk>/add-products/', add_products_to_record, name='add_products_to_record'),
    path('record/<int:pk>/clear-products/', clear_products, name='clear_products'),
    path('record/<int:pk>/export-products/', export_products, name='export_products'),
    path('record/<int:pk>/delete/', delete_record, name='delete_record'),
    path('record/<int:pk>/add-file/', add_file, name='add_file'),
    path('file/<int:file_id>/delete/', delete_file, name='delete_file'),
    path('process-csv/', process_csv, name='process_csv'),
    path('process-csv/<int:pk>/', process_csv_by_pk, name='process_csv_by_pk'),
    path('register/', register_user, name='register'),
    path('logout/', logout_user, name='logout'),
    path('add-record/', add_record, name='add_record'),
    path('record/<int:pk>/update/', update_record, name='update_record'),
    path('record/<int:pk>/set-margin/', set_margin_flags, name='set_margin_flags'),
    path('record/<int:pk>/update-status/', update_record_status, name='update_record_status'),
    path('product/<int:pk>/', product_detail, name='product_detail'),
    path('unplanned-expenses/', unplanned_expenses_list, name='unplanned_expenses_list'),
    path('unplanned-expenses/edit/<int:pk>/', edit_unplanned_expense, name='edit_unplanned_expense'),
    path('analytics/', analytics_dashboard, name='analytics_dashboard'),
    path('payments/', payments_page, name='payments_page'),
    path('payments/<int:payment_id>/mark-paid/', mark_payment_paid, name='mark_payment_paid'),
    path('payments/<int:payment_id>/mark-unpaid/', mark_payment_unpaid, name='mark_payment_unpaid'),
    path('ufaloft/start/', start_ufaloft_watch, name='start_ufaloft_watch'),
    path('ufaloft/ui/', ufaloft_ui, name='ufaloft_ui'),
    path('profile/', my_profile, name='my_profile'),
    path('profiles/', profiles_list, name='profiles_list'),
    path('profiles/<int:user_id>/', staff_profile, name='staff_profile'),
    path('customer/<int:user_id>/', customer_detail, name='customer_detail'),
    path('create_product/', create_product, name='create_product'),
    path('products/', products_list, name='products_list'),
    path('categories/create/', create_category, name='create_category'),

]