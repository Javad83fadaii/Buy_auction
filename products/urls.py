from django.urls import path

from .views import ProductCreateView, ProductDetailView, ProductEditView, ProductListView

app_name = 'products'

urlpatterns = [
    path('', ProductListView.as_view(), name='list'),
    path('<int:id>/', ProductDetailView.as_view(), name='detail'),
    path('<int:id>/edit/', ProductEditView.as_view(), name='edit'),
    path('create/', ProductCreateView.as_view(), name='create'),
]
