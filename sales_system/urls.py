from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('sales.urls')),
    path('monitoring/', include('monitoring.urls')),
    path('exchange/', include('exchange.urls')),
    path('staff/', include('staff.urls')),
    path('transport/', include('transport.urls')),
    path('docs/', include('docs_lab.urls')),
]
