from django.urls import path
from . import views

app_name = 'overtime'

urlpatterns = [
    path('', views.overtime_list, name='overtime_list'),
    path('my-tasks/', views.my_tasks, name='my_tasks'),
    path('queue/<str:queue_type>/', views.overtime_queue, name='overtime_queue'),
    path('create/', views.overtime_create, name='overtime_create'),
    path('<int:pk>/', views.overtime_detail, name='overtime_detail'),
    path('<int:pk>/update/', views.overtime_update, name='overtime_update'),
    path('<int:pk>/cancel/', views.overtime_cancel, name='overtime_cancel'),
    path('<int:pk>/approve/admin/', views.admin_approve, name='admin_approve'),
    path('<int:pk>/approve/factory/', views.factory_approve, name='factory_approve'),
    path('<int:pk>/approve/management/', views.management_approve, name='management_approve'),
]