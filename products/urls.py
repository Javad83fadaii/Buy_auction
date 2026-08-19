from django.urls import path

from .views import ProductCreateView

app_name = 'products'

urlpatterns = [
    path('create/', ProductCreateView.as_view(), name='create'),
]
