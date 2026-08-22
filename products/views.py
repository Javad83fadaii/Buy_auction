import logging
from urllib.parse import urlencode

from django.contrib import messages
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db.models import F, Prefetch, Q
from django.db.models.functions import Trim
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView

from accounts.permissions import RolePermissionMixin

from .choices import ProductSourceTypeChoices, ProductStatusChoices
from .forms import (
    PRODUCT_LIST_DEFAULT_SORT,
    PRODUCT_LIST_SORT_CHOICES,
    ProductCreateForm,
    ProductListFilterForm,
)
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
    status_filter_labels = {
        ProductStatusChoices.DRAFT: 'پیش‌نویس',
        ProductStatusChoices.PENDING_REVIEW: 'در انتظار بررسی',
        ProductStatusChoices.APPROVED: 'تأیید شده',
        ProductStatusChoices.PUBLISHED: 'منتشر شده',
        ProductStatusChoices.REJECTED: 'رد شده',
    }
    source_filter_labels = {
        ProductSourceTypeChoices.MANUAL: 'پیشنهاد دستی',
        ProductSourceTypeChoices.CHRISTIES: 'کریستیز',
        ProductSourceTypeChoices.SOTHEBYS: 'ساتبیز',
        ProductSourceTypeChoices.OTHER_AUCTION: 'سایر حراجی‌ها',
    }
    default_sort = PRODUCT_LIST_DEFAULT_SORT
    allowed_sorts = {
        '-created_at': ('-created_at', '-pk'),
        'created_at': ('created_at', 'pk'),
        'title': ('title', 'pk'),
        '-title': ('-title', '-pk'),
        'suitable_price': (F('suitable_price').asc(nulls_last=True), 'pk'),
        '-suitable_price': (F('suitable_price').desc(nulls_last=True), '-pk'),
    }

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
        status_filter = self.get_status_filter()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        source_filter = self.get_source_filter()
        if source_filter:
            queryset = queryset.filter(source_type=source_filter)
        art_type_filter = self.get_art_type_filter()
        if art_type_filter:
            queryset = queryset.annotate(normalized_art_type=Trim('art_type')).filter(
                normalized_art_type=art_type_filter
            )
        date_from_filter = self.get_date_from_filter()
        if date_from_filter:
            queryset = queryset.filter(suggestion_date__gte=date_from_filter)
        date_to_filter = self.get_date_to_filter()
        if date_to_filter:
            queryset = queryset.filter(suggestion_date__lte=date_to_filter)
        queryset = queryset.order_by(*self.allowed_sorts[self.get_selected_sort()])
        return queryset

    def get_filter_form(self):
        if not hasattr(self, '_filter_form'):
            self._filter_form = ProductListFilterForm(self.request.GET)
            self._filter_form.is_valid()
        return self._filter_form

    def get_search_query(self):
        return self.request.GET.get('q', '').strip()

    def get_status_filter(self):
        status_filter = self.request.GET.get('status', '').strip()
        if status_filter in ProductStatusChoices.values:
            return status_filter
        return ''

    def get_source_filter(self):
        source_filter = self.request.GET.get('source', '').strip()
        if source_filter in ProductSourceTypeChoices.values:
            return source_filter
        return ''

    def get_art_type_filter(self):
        return self.request.GET.get('art_type', '').strip()

    def get_date_from_filter(self):
        return self.get_filter_form().cleaned_data.get('date_from')

    def get_date_to_filter(self):
        return self.get_filter_form().cleaned_data.get('date_to')

    def get_selected_sort(self):
        return self.get_filter_form().cleaned_data.get('sort', self.default_sort)

    def get_status_options(self):
        return [
            {'value': value, 'label': self.status_filter_labels[value]}
            for value in ProductStatusChoices.values
        ]

    def get_source_options(self):
        return [
            {'value': value, 'label': self.source_filter_labels[value]}
            for value in ProductSourceTypeChoices.values
        ]

    def get_art_type_options(self):
        art_type_queryset = (
            Product.objects.annotate(normalized_art_type=Trim('art_type'))
            .exclude(normalized_art_type='')
            .values_list('normalized_art_type', flat=True)
            .order_by('normalized_art_type')
            .distinct()
        )
        return list(art_type_queryset)

    def get_sort_options(self):
        return [
            {'value': value, 'label': label}
            for value, label in PRODUCT_LIST_SORT_CHOICES
        ]

    def get_pagination_query(self):
        query_data = self.request.GET.copy()
        query_data.pop('page', None)
        return query_data.urlencode()

    def get_clear_filters_url(self):
        search_query = self.get_search_query()
        if not search_query:
            return self.request.path
        return f'{self.request.path}?{urlencode({"q": search_query})}'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_query = self.get_search_query()
        selected_status = self.get_status_filter()
        selected_source = self.get_source_filter()
        selected_art_type = self.get_art_type_filter()
        filter_form = self.get_filter_form()
        selected_sort = self.get_selected_sort()
        context['page_title'] = 'لیست محصولات'
        context['search_query'] = search_query
        context['selected_status'] = selected_status
        context['selected_source'] = selected_source
        context['selected_art_type'] = selected_art_type
        context['filter_form'] = filter_form
        context['selected_sort'] = selected_sort
        context['default_sort'] = self.default_sort
        context['status_options'] = self.get_status_options()
        context['source_options'] = self.get_source_options()
        context['art_type_options'] = self.get_art_type_options()
        context['sort_options'] = self.get_sort_options()
        context['has_art_type_options'] = bool(context['art_type_options'])
        context['pagination_query'] = self.get_pagination_query()
        context['clear_filters_url'] = self.get_clear_filters_url()
        context['has_active_filters'] = bool(
            selected_status
            or selected_source
            or selected_art_type
            or filter_form['date_from'].value()
            or filter_form['date_to'].value()
            or selected_sort != self.default_sort
        )
        return context
