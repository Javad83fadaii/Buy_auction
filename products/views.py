import logging

from django.contrib import messages
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db.models import Prefetch, Q
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView

from accounts.permissions import RolePermissionMixin

from .forms import ProductCreateForm
from .models import Product, ProductImage
from .services import create_manual_product

logger = logging.getLogger(__name__)


class ProductCreateView(RolePermissionMixin, FormView):
    template_name = 'products/product_create.html'
    form_class = ProductCreateForm
    permission_required = 'products.add_product'
    success_url = reverse_lazy('products:create')

    def form_valid(self, form):
        try:
            create_manual_product(
                cleaned_data=form.cleaned_data,
                images=form.cleaned_data.get('images', []),
                user=self.request.user,
            )
        except ValidationError as exc:
            self._apply_validation_errors(form, exc)
            return self.form_invalid(form)
        except Exception:
            logger.exception('Product creation failed for user %s', self.request.user.pk)
            form.add_error(None, 'ثبت اثر با خطا مواجه شد. لطفاً دوباره تلاش کنید.')
            return self.form_invalid(form)

        messages.success(self.request, 'اثر با موفقیت ثبت شد.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'ثبت پیشنهاد جدید'
        return context

    def _apply_validation_errors(self, form, exc: ValidationError) -> None:
        if hasattr(exc, 'message_dict'):
            for field_name, errors in exc.message_dict.items():
                target_field = None if field_name == NON_FIELD_ERRORS else field_name
                if target_field and target_field not in form.fields:
                    target_field = None
                for error in errors:
                    form.add_error(target_field, error)
            return

        for error in exc.messages:
            form.add_error(None, error)


class ProductListView(RolePermissionMixin, ListView):
    template_name = 'products/product_list.html'
    permission_required = 'products.view_product'
    model = Product
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        primary_image_queryset = ProductImage.objects.filter(is_primary=True).only(
            'id',
            'product_id',
            'image',
            'is_primary',
        )
        queryset = (
            Product.objects.all()
            .prefetch_related(
                Prefetch(
                    'images',
                    queryset=primary_image_queryset,
                    to_attr='primary_images',
                )
            )
        )
        search_query = self.get_search_query()
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query)
                | Q(product_code__icontains=search_query)
                | Q(artist__icontains=search_query)
                | Q(suggested_by__icontains=search_query)
            )
        return queryset

    def get_search_query(self):
        return self.request.GET.get('q', '').strip()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'لیست محصولات'
        context['search_query'] = self.get_search_query()
        return context
