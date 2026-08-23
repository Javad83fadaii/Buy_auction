from django.urls import path

from .views import ProductCreateView, ProductDetailView, ProductListView

app_name = 'products'

urlpatterns = [
    path('', ProductListView.as_view(), name='list'),
    path('<int:id>/', ProductDetailView.as_view(), name='detail'),
    path('create/', ProductCreateView.as_view(), name='create'),
]
