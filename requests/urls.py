from django.urls import path
from . import views

app_name = 'requests'

urlpatterns = [
    path('', views.request_list, name='request_list'),
    path('my-tasks/', views.my_tasks, name='my_tasks'),
    path('queue/<str:queue_type>/', views.request_queue, name='request_queue'),
    path('create/', views.request_create, name='request_create'),
    path('<int:pk>/', views.request_detail, name='request_detail'),
    path('<int:pk>/update/', views.request_update, name='request_update'),
    path('<int:pk>/cancel/', views.cancel_request, name='cancel_request'),
    path('<int:pk>/approve/creator/', views.approve_creator, name='approve_creator'),
    path('<int:pk>/approve/factory/', views.approve_factory, name='approve_factory'),
    path('<int:pk>/approve/management/', views.approve_management, name='approve_management'),
]