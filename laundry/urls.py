from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/create/', views.order_create, name='order_create'),
    path('orders/edit/<int:pk>/', views.order_edit, name='order_edit'),
    path('orders/status/<int:order_id>/<str:status>/', views.update_order_status, name='update_order_status'),
    path('orders/payment/<int:order_id>/<str:payment_status>/', views.update_order_payment, name='update_order_payment'),
    path('orders/mark-all-ready-completed/', views.mark_all_ready_completed, name='mark_all_ready_completed'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.customer_create, name='customer_create'),
    path('customers/edit/<int:pk>/', views.customer_edit, name='customer_edit'),
    path('customers/find-by-phone/<str:phone>/', views.find_customer_by_phone, name='find_customer_by_phone'),
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/create/', views.expense_create, name='expense_create'),
    path('expenses/edit/<int:pk>/', views.expense_edit, name='expense_edit'),
    path('reports/', views.reports, name='reports'),
    path('receipt/<int:order_id>/', views.receipt, name='receipt'),
    path('logout/', views.logout_view, name='logout'),
]