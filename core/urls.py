from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    
    path('my-all-requests/', views.my_all_requests, name='my_all_requests'),
    
    path('my-tasks/', views.MyTasksView.as_view(), name='my_all_tasks'),
]