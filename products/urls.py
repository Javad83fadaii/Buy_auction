from django.urls import path

from .views import (
    ProductApproveView,
    ProductCancelToggleView,
    ProductCreateView,
    ProductDashboardView,
    ProductDetailView,
    ProductEditView,
    ProductImageDeleteView,
    ProductImageSetPrimaryView,
    ProductImageSortOrderUpdateView,
    ProductImageUploadView,
    ProductListView,
    ProductPublishView,
    ProductRejectView,
    ProductReReviewView,
    ProductSubmitReviewView,
)

app_name = 'products'

urlpatterns = [
    path('', ProductListView.as_view(), name='list'),
    path('dashboard/', ProductDashboardView.as_view(), name='dashboard'),
    path('<int:id>/', ProductDetailView.as_view(), name='detail'),
    path('<int:id>/submit-review/', ProductSubmitReviewView.as_view(), name='submit_review'),
    path('<int:id>/approve/', ProductApproveView.as_view(), name='approve'),
    path('<int:id>/reject/', ProductRejectView.as_view(), name='reject'),
    path('<int:id>/publish/', ProductPublishView.as_view(), name='publish'),
    path('<int:id>/re-review/', ProductReReviewView.as_view(), name='re_review'),
    path('<int:id>/cancel-toggle/', ProductCancelToggleView.as_view(), name='cancel_toggle'),
    path('<int:id>/images/upload/', ProductImageUploadView.as_view(), name='image_upload'),
    path(
        '<int:id>/images/<int:image_id>/primary/',
        ProductImageSetPrimaryView.as_view(),
        name='image_set_primary',
    ),
    path(
        '<int:id>/images/<int:image_id>/sort/',
        ProductImageSortOrderUpdateView.as_view(),
        name='image_sort_update',
    ),
    path(
        '<int:id>/images/<int:image_id>/delete/',
        ProductImageDeleteView.as_view(),
        name='image_delete',
    ),
    path('<int:id>/edit/', ProductEditView.as_view(), name='edit'),
    path('create/', ProductCreateView.as_view(), name='create'),
]
