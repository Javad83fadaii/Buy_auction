from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from accounts.views import DashboardView, OperatorDashboardView
from config.views import home

urlpatterns = [
    path('', home, name='home'),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('dashboard/operator/', OperatorDashboardView.as_view(), name='operator_dashboard'),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
