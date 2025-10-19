from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('record/<int:pk>/excel-data/', views.get_excel_data, name='get_excel_data'),
    path('record/<int:pk>/save-excel/', views.save_excel_data, name='save_excel_data'),
    path('record/<int:pk>/download-excel/', views.download_excel_file, name='download_excel_file'),
    path('record/<int:pk>/add-expense/', views.add_unplanned_expense, name='add_unplanned_expense'),
    path('unplanned-expenses/delete/<int:pk>/', views.delete_unplanned_expense, name='delete_unplanned_expense'),
    path('record/<int:pk>/', views.record_detail, name='record_detail'),
    path('record/<int:pk>/designer-manual/', views.set_designer_manual_salary, name='set_designer_manual_salary'),
    path('record/<int:pk>/add-products/', views.add_products_to_record, name='add_products_to_record'),
    path('record/<int:pk>/clear-products/', views.clear_products, name='clear_products'),
    path('record/<int:pk>/export-products/', views.export_products, name='export_products'),
    path('record/<int:pk>/delete/', views.delete_record, name='delete_record'),
    path('file/<int:file_id>/delete/', views.delete_file, name='delete_file'),
    path('process-csv/', views.process_csv, name='process_csv'),
    path('process-csv/<int:pk>/', views.process_csv_by_pk, name='process_csv_by_pk'),
    path('register/', views.register_user, name='register'),
    path('logout/', views.logout_user, name='logout'),
    path('add-record/', views.add_record, name='add_record'),
    path('record/<int:pk>/update/', views.update_record, name='update_record'),
    path('record/<int:pk>/set-margin/', views.set_margin_flags, name='set_margin_flags'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('unplanned-expenses/', views.unplanned_expenses_list, name='unplanned_expenses_list'),

    path('unplanned-expenses/edit/<int:pk>/', views.edit_unplanned_expense, name='edit_unplanned_expense'),
    
    # Аналитика
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),

]