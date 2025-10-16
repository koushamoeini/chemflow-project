from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    # URL های اصلی
    path("", views.order_list, name="order_list"),
    path("new/", views.order_create, name="order_create"),
    path("<int:pk>/", views.order_detail, name="order_details"),
    path("<int:pk>/edit/", views.order_update, name="order_update"),
    path("<int:pk>/cancel/", views.cancel_order, name="cancel_order"),
    path("<int:pk>/approve/<str:approval_type>/", views.approve_order, name="approve_order"),

    # URL یکپارچه برای لیست‌های انتظار
    path("pending/<str:queue_type>/", views.pending_orders, name="pending_orders"),

    # URL وظایف من
    path("tasks/", views.my_tasks, name="my_tasks"),

    # URL های Autocomplete
    path('customer-autocomplete/', views.customer_autocomplete, name='customer_autocomplete'),
    path('product-autocomplete/', views.product_autocomplete, name='product_autocomplete'),

]