import logging
from urllib.parse import urlencode

from django.contrib import messages
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db.models import Count, F, Prefetch, Q
from django.db.models.functions import Trim
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, FormView, ListView, TemplateView, UpdateView, View

from accounts.permissions import RolePermissionMixin

from .choices import ProductSourceTypeChoices, ProductStatusChoices
from .forms import (
    PRODUCT_LIST_DEFAULT_SORT,
    PRODUCT_LIST_SORT_CHOICES,
    ProductCreateForm,
    ProductEditForm,
    ProductImageSortOrderForm,
    ProductImageUploadForm,
    ProductListFilterForm,
)
from .models import Product, ProductImage
from .services import (
    add_product_image,
    create_manual_product,
    delete_product_image,
    get_available_status_transitions,
    set_product_image_primary,
    update_product_cancelled_state,
    update_product_image_sort_order,
    update_product_review_status,
)

logger = logging.getLogger(__name__)


class ProductDisplayLabelsMixin:
    status_filter_labels = {
        ProductStatusChoices.DRAFT: 'پیش‌نویس',
        ProductStatusChoices.PENDING_REVIEW: 'در انتظار بررسی',
        ProductStatusChoices.APPROVED: 'تأیید شده',
        ProductStatusChoices.PUBLISHED: 'منتشر شده',
        ProductStatusChoices.REJECTED: 'رد شده',
    }
    source_filter_labels = {
        ProductSourceTypeChoices.MANUAL: 'ثبت دستی',
        ProductSourceTypeChoices.CHRISTIES: "Christie's",
        ProductSourceTypeChoices.SOTHEBYS: "Sotheby's",
        ProductSourceTypeChoices.OTHER_AUCTION: 'سایر مزایده‌ها',
    }

    def get_status_label(self, product: Product) -> str:
        return self.status_filter_labels.get(product.status, product.get_status_display())

    def get_source_label(self, product: Product) -> str:
        return self.source_filter_labels.get(product.source_type, product.get_source_type_display())


class ProductDashboardView(RolePermissionMixin, TemplateView):
    template_name = 'products/product_dashboard.html'
    permission_required = 'products.add_product'

    def get_statistics(self) -> list[dict[str, str | int]]:
        stats = Product.objects.aggregate(
            total_products=Count('id'),
            active_products=Count('id', filter=Q(is_cancelled=False)),
            cancelled_products=Count('id', filter=Q(is_cancelled=True)),
            pending_review_products=Count(
                'id',
                filter=Q(status=ProductStatusChoices.PENDING_REVIEW),
            ),
            approved_products=Count(
                'id',
                filter=Q(status=ProductStatusChoices.APPROVED),
            ),
            published_products=Count(
                'id',
                filter=Q(status=ProductStatusChoices.PUBLISHED),
            ),
        )
        return [
            {'label': 'کل محصولات', 'count': stats['total_products'], 'accent': 'primary'},
            {'label': 'محصولات فعال', 'count': stats['active_products'], 'accent': 'success'},
            {'label': 'محصولات لغوشده', 'count': stats['cancelled_products'], 'accent': 'warning'},
            {
                'label': 'در انتظار بررسی',
                'count': stats['pending_review_products'],
                'accent': 'warning',
            },
            {'label': 'تأیید شده', 'count': stats['approved_products'], 'accent': 'success'},
            {'label': 'منتشر شده', 'count': stats['published_products'], 'accent': 'info'},
        ]

    def get_recent_products(self):
        return (
            Product.objects.select_related('created_by')
            .order_by('-created_at', '-pk')[:5]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'مدیریت محصولات'
        context['statistics'] = self.get_statistics()
        context['recent_products'] = list(self.get_recent_products())
        context['can_review_products'] = self.request.user.has_perm('products.review_product')
        context['pending_review_url'] = (
            f"{reverse('products:list')}?{urlencode({'status': ProductStatusChoices.PENDING_REVIEW})}"
        )
        return context


class ProductDetailContextMixin(ProductDisplayLabelsMixin):
    template_name = 'products/product_detail.html'
    pk_url_kwarg = 'id'

    def get_product_queryset(self):
        image_queryset = ProductImage.objects.only(
            'id',
            'product_id',
            'image',
            'is_primary',
            'sort_order',
        ).order_by('sort_order', 'id')
        return Product.objects.select_related('created_by', 'updated_by').prefetch_related(
            Prefetch('images', queryset=image_queryset)
        )

    def get_product(self):
        if not hasattr(self, '_product'):
            self._product = get_object_or_404(
                self.get_product_queryset(),
                pk=self.kwargs[self.pk_url_kwarg],
            )
        return self._product

    def get_back_url(self) -> str:
        next_url = self.request.GET.get('next', '').strip()
        if next_url.startswith('/products/'):
            return next_url
        return reverse('products:list')

    def get_primary_image(self, gallery_images: list[ProductImage]) -> ProductImage | None:
        primary_image = next((image for image in gallery_images if image.is_primary), None)
        if primary_image is None and gallery_images:
            primary_image = gallery_images[0]
        return primary_image

    def get_image_upload_form(self):
        return ProductImageUploadForm()

    def build_managed_images(self, gallery_images, image_sort_forms=None):
        bound_forms = image_sort_forms or {}
        return [
            {
                'image': image,
                'sort_form': bound_forms.get(image.pk)
                or ProductImageSortOrderForm(prefix=f'image-{image.pk}', instance=image),
            }
            for image in gallery_images
        ]

    def get_detail_context(self, *, product=None, image_upload_form=None, image_sort_forms=None):
        product = product or self.get_product()
        gallery_images = list(product.images.all())
        primary_image = self.get_primary_image(gallery_images)
        can_review_product = self.request.user.has_perm('products.review_product')
        available_status_transitions = get_available_status_transitions(product=product)

        return {
            'page_title': product.title,
            'product': product,
            'primary_image': primary_image,
            'gallery_images': gallery_images,
            'managed_images': self.build_managed_images(gallery_images, image_sort_forms=image_sort_forms),
            'image_upload_form': image_upload_form or self.get_image_upload_form(),
            'can_manage_images': self.request.user.has_perm('products.change_product'),
            'can_review_product': can_review_product,
            'show_submit_review_action': (
                can_review_product and ProductStatusChoices.PENDING_REVIEW in available_status_transitions
            ),
            'show_approve_action': (
                can_review_product and ProductStatusChoices.APPROVED in available_status_transitions
            ),
            'show_reject_action': (
                can_review_product and ProductStatusChoices.REJECTED in available_status_transitions
            ),
            'show_publish_action': (
                can_review_product and ProductStatusChoices.PUBLISHED in available_status_transitions
            ),
            'show_rereview_action': (
                can_review_product and ProductStatusChoices.PENDING_REVIEW in available_status_transitions
            ),
            'status_label': self.get_status_label(product),
            'source_label': self.get_source_label(product),
            'back_url': self.get_back_url(),
        }

    def render_detail_response(self, *, status=200, image_upload_form=None, image_sort_forms=None):
        return self.render_to_response(
            self.get_detail_context(
                image_upload_form=image_upload_form,
                image_sort_forms=image_sort_forms,
            ),
            status=status,
        )

    def apply_validation_errors(self, form, exc: ValidationError) -> None:
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


class ProductCreateView(RolePermissionMixin, FormView):
    template_name = 'products/product_create.html'
    form_class = ProductCreateForm
    permission_required = 'products.add_product'

    def form_valid(self, form):
        try:
            self.object = create_manual_product(
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
        return redirect(self.get_success_url())

    def get_success_url(self):
        if hasattr(self, 'object') and self.object is not None:
            return reverse('products:detail', args=[self.object.pk])
        return reverse_lazy('products:create')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'ثبت محصول'
        context['cancel_url'] = reverse('products:list')
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


class ProductListView(ProductDisplayLabelsMixin, RolePermissionMixin, ListView):
    template_name = 'products/product_list.html'
    permission_required = 'products.view_product'
    model = Product
    context_object_name = 'products'
    paginate_by = 20
    default_sort = PRODUCT_LIST_DEFAULT_SORT
    cancelled_filter_options = (
        {'value': 'all', 'label': 'همه'},
        {'value': '0', 'label': 'فعال'},
        {'value': '1', 'label': 'لغو شده'},
    )
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
        cancelled_filter = self.get_cancelled_filter()
        if cancelled_filter == '1':
            queryset = queryset.filter(is_cancelled=True)
        elif cancelled_filter == '0':
            queryset = queryset.filter(is_cancelled=False)
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

    def get_cancelled_filter(self):
        cancelled_filter = self.request.GET.get('cancelled', 'all').strip()
        if cancelled_filter in {'all', '0', '1'}:
            return cancelled_filter
        return 'all'

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

    def get_cancelled_filter_options(self):
        return list(self.cancelled_filter_options)

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
        selected_cancelled = self.get_cancelled_filter()
        filter_form = self.get_filter_form()
        selected_sort = self.get_selected_sort()
        context['page_title'] = 'لیست محصولات'
        context['search_query'] = search_query
        context['selected_status'] = selected_status
        context['selected_source'] = selected_source
        context['selected_art_type'] = selected_art_type
        context['selected_cancelled'] = selected_cancelled
        context['filter_form'] = filter_form
        context['selected_sort'] = selected_sort
        context['default_sort'] = self.default_sort
        context['status_options'] = self.get_status_options()
        context['source_options'] = self.get_source_options()
        context['art_type_options'] = self.get_art_type_options()
        context['sort_options'] = self.get_sort_options()
        context['cancelled_filter_options'] = self.get_cancelled_filter_options()
        context['has_art_type_options'] = bool(context['art_type_options'])
        context['pagination_query'] = self.get_pagination_query()
        context['clear_filters_url'] = self.get_clear_filters_url()
        context['has_active_filters'] = bool(
            selected_status
            or selected_source
            or selected_art_type
            or selected_cancelled != 'all'
            or filter_form['date_from'].value()
            or filter_form['date_to'].value()
            or selected_sort != self.default_sort
        )
        return context


class ProductDetailView(ProductDetailContextMixin, RolePermissionMixin, DetailView):
    permission_required = 'products.view_product'
    model = Product
    context_object_name = 'product'
    pk_url_kwarg = 'id'

    def get_queryset(self):
        return self.get_product_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_detail_context(product=context['product']))
        return context


class ProductEditView(RolePermissionMixin, UpdateView):
    template_name = 'products/product_edit.html'
    form_class = ProductEditForm
    permission_required = 'products.change_product'
    model = Product
    context_object_name = 'product'
    pk_url_kwarg = 'id'

    def get_queryset(self):
        return Product.objects.select_related('created_by', 'updated_by')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'محصول با موفقیت ویرایش شد.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('products:detail', args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'ویرایش محصول'
        context['cancel_url'] = reverse('products:detail', args=[self.object.pk])
        return context


class ProductImageManagementMixin(ProductDetailContextMixin, RolePermissionMixin):
    permission_required = 'products.change_product'

    def get_success_url(self):
        return reverse('products:detail', args=[self.get_product().pk])

    def get_image(self):
        if not hasattr(self, '_image'):
            self._image = get_object_or_404(
                ProductImage.objects.select_related('product'),
                pk=self.kwargs['image_id'],
                product=self.get_product(),
            )
        return self._image


class ProductImageUploadView(ProductImageManagementMixin, FormView):
    form_class = ProductImageUploadForm
    http_method_names = ['post']

    def form_valid(self, form):
        try:
            add_product_image(
                product=self.get_product(),
                image=form.cleaned_data['image'],
            )
        except ValidationError as exc:
            self.apply_validation_errors(form, exc)
            return self.form_invalid(form)

        messages.success(self.request, 'تصویر با موفقیت بارگذاری شد.')
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        return self.render_detail_response(status=200, image_upload_form=form)


class ProductImageSortOrderUpdateView(ProductImageManagementMixin, FormView):
    form_class = ProductImageSortOrderForm
    http_method_names = ['post']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.get_image()
        kwargs['prefix'] = f'image-{self.get_image().pk}'
        return kwargs

    def form_valid(self, form):
        try:
            update_product_image_sort_order(
                product=self.get_product(),
                image=self.get_image(),
                sort_order=form.cleaned_data['sort_order'],
            )
        except ValidationError as exc:
            self.apply_validation_errors(form, exc)
            return self.form_invalid(form)

        messages.success(self.request, 'ترتیب تصویر با موفقیت ذخیره شد.')
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        return self.render_detail_response(
            status=200,
            image_sort_forms={self.get_image().pk: form},
        )


class ProductImageSetPrimaryView(ProductImageManagementMixin, View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        set_product_image_primary(
            product=self.get_product(),
            image=self.get_image(),
        )
        messages.success(request, 'تصویر اصلی با موفقیت تغییر کرد.')
        return redirect(self.get_success_url())


class ProductImageDeleteView(ProductImageManagementMixin, View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        delete_product_image(
            product=self.get_product(),
            image=self.get_image(),
        )
        messages.success(request, 'تصویر با موفقیت حذف شد.')
        return redirect(self.get_success_url())


class ProductCancelToggleView(RolePermissionMixin, View):
    permission_required = 'products.change_product'
    http_method_names = ['post']

    def get_product(self):
        if not hasattr(self, '_product'):
            self._product = get_object_or_404(Product, pk=self.kwargs['id'])
        return self._product

    def get_success_url(self):
        return reverse('products:detail', args=[self.get_product().pk])

    def post(self, request, *args, **kwargs):
        product = self.get_product()
        activate = request.POST.get('action') == 'restore'
        updated_product = update_product_cancelled_state(
            product=product,
            is_cancelled=not activate,
            user=request.user,
        )
        if updated_product.is_cancelled:
            messages.success(request, 'محصول با موفقیت لغو شد.')
        else:
            messages.success(request, 'محصول با موفقیت فعال‌سازی مجدد شد.')
        return redirect(self.get_success_url())


class ProductReviewActionView(RolePermissionMixin, View):
    permission_required = 'products.review_product'
    http_method_names = ['post']
    target_status = ''
    success_message = ''

    def get_product(self):
        if not hasattr(self, '_product'):
            self._product = get_object_or_404(Product, pk=self.kwargs['id'])
        return self._product

    def get_success_url(self):
        return reverse('products:detail', args=[self.get_product().pk])

    def post(self, request, *args, **kwargs):
        try:
            update_product_review_status(
                product=self.get_product(),
                status=self.target_status,
                user=request.user,
            )
        except ValidationError as exc:
            messages.error(request, exc.messages[0] if exc.messages else 'تغییر وضعیت ممکن نیست.')
            return redirect(self.get_success_url())

        messages.success(request, self.success_message)
        return redirect(self.get_success_url())


class ProductApproveView(ProductReviewActionView):
    target_status = ProductStatusChoices.APPROVED
    success_message = 'محصول با موفقیت تأیید شد.'


class ProductSubmitReviewView(ProductReviewActionView):
    target_status = ProductStatusChoices.PENDING_REVIEW
    success_message = 'محصول با موفقیت برای بررسی ارسال شد.'


class ProductRejectView(ProductReviewActionView):
    target_status = ProductStatusChoices.REJECTED
    success_message = 'محصول با موفقیت رد شد.'


class ProductPublishView(ProductReviewActionView):
    target_status = ProductStatusChoices.PUBLISHED
    success_message = 'محصول با موفقیت منتشر شد.'


class ProductReReviewView(ProductReviewActionView):
    target_status = ProductStatusChoices.PENDING_REVIEW
    success_message = 'محصول با موفقیت برای بررسی مجدد ارسال شد.'
