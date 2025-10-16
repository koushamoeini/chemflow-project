from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("", include("core.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("orders/", include(("orders.urls", "orders"), namespace="orders")),
    path("planning/", include(("planning.urls", "planning"), namespace="planning")),
    path('requests/', include(('requests.urls', 'requests'), namespace='requests')),
    path('overtime/', include(('overtime.urls', 'overtime'), namespace='overtime')),

]



