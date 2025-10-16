from django.urls import path
from .views import ready_orders
from . import views

app_name = "planning"

urlpatterns = [
    path("ready-orders/", ready_orders, name="ready_orders"),
    path("order/<int:pk>/toggle-planning/", views.toggle_planning_status, name="toggle_planning"),    path("tasks/", views.my_tasks, name="my_tasks"),
    
    
    path("production/", views.prodreq_list, name="prodreq_list"),
    path("production/new/", views.prodreq_create, name="prodreq_create"),
    path("production/<int:pk>/", views.prodreq_detail, name="prodreq_detail"),
    path("production/<int:pk>/edit/", views.prodreq_update, name="prodreq_update"),
    path("production/<int:pk>/sign/planning/", views.sign_planning, name="sign_planning"),
    path("production/<int:pk>/sign/factory/", views.sign_factory, name="sign_factory"),
    path("pending/planning/", views.pending_planning, name="pending_planning"),
    path("pending/factory/", views.pending_factory, name="pending_factory"),
     
]
