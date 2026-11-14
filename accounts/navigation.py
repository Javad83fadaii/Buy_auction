from urllib.parse import urlencode

from django.urls import reverse

from products.choices import ProductSourceTypeChoices, ProductStatusChoices


def build_url(view_name: str, **params) -> str:
    base_url = reverse(view_name)
    filtered_params = {key: value for key, value in params.items() if value not in (None, '', [])}
    if not filtered_params:
        return base_url
    return f'{base_url}?{urlencode(filtered_params)}'


def _get_view_name(request) -> str:
    resolver_match = getattr(request, 'resolver_match', None)
    return getattr(resolver_match, 'view_name', '') or ''


def _is_filtered_product_list(request, *, status: str = '', source: str = '') -> bool:
    if _get_view_name(request) != 'products:list':
        return False
    if status and request.GET.get('status', '').strip() != status:
        return False
    if source and request.GET.get('source', '').strip() != source:
        return False
    return True


def _is_active_link(request, *, key: str) -> bool:
    view_name = _get_view_name(request)
    if key in {'dashboard', 'dashboard_products'}:
        return view_name == 'dashboard'
    if key == 'auction_list':
        return view_name in {
            'products:auction_list',
            'products:auction_detail',
            'products:auction_create',
            'products:auction_edit',
            'products:auction_sync',
        }
    if key == 'statistics':
        return view_name == 'statistics'
    if key == 'create_product':
        return view_name == 'products:create'
    if key == 'scraper_import':
        return view_name == 'products:scraper_import'
    if key == 'rejected_products':
        return _is_filtered_product_list(
            request,
            status=ProductStatusChoices.REJECTED,
        )
    if key == 'manual_products':
        return _is_filtered_product_list(
            request,
            source=ProductSourceTypeChoices.MANUAL,
        )
    if key == 'all_products':
        if view_name in {'products:detail', 'products:edit'}:
            return True
        return _is_filtered_product_list(request) and not any(
            (
                request.GET.get('status', '').strip() == ProductStatusChoices.REJECTED,
                request.GET.get('source', '').strip() == ProductSourceTypeChoices.MANUAL,
            )
        )
    if key == 'operator_dashboard':
        return view_name == 'operator_dashboard'
    if key == 'change_password':
        return view_name == 'accounts:change_password'
    return False


def _build_link(request, *, key: str, label: str, url: str, variant: str = 'secondary') -> dict[str, object]:
    return {
        'key': key,
        'label': label,
        'url': url,
        'variant': variant,
        'is_active': _is_active_link(request, key=key),
    }


def build_quick_links(request) -> list[dict[str, object]]:
    """Quick navigation links shared by the dashboard sidebar across all pages."""
    user = request.user
    if not user.is_authenticated:
        return []

    quick_links = []

    if user.is_superuser:
        quick_links.append(_build_link(
            request,
            key='change_password',
            label='تغییر رمز',
            url=reverse('accounts:change_password'),
        ))

    if user.has_perm('products.add_product'):
        quick_links = [
            *(
                [
                    _build_link(
                        request,
                        key='dashboard',
                        label='داشبورد',
                        url=reverse('dashboard'),
                        variant='primary',
                    ),
                ]
                if user.is_superuser
                else []
            ),
            _build_link(
                request,
                key='auction_list',
                label='لیست حراجیها',
                url=reverse('products:auction_list'),
                variant='primary',
            ),
            _build_link(
                request,
                key='statistics',
                label='آمار و گزارشات',
                url=reverse('statistics'),
                variant='primary',
            ),
            *(
                [
                    _build_link(
                        request,
                        key='create_product',
                        label='ثبت محصول',
                        url=reverse('products:create'),
                    ),
                    _build_link(
                        request,
                        key='scraper_import',
                        label='ایمپورت اسکرپر',
                        url=reverse('products:scraper_import'),
                    ),
                ]
                if user.is_superuser
                else []
            ),
            _build_link(
                request,
                key='manual_products',
                label='محصولات دستی',
                url=build_url(
                    'products:list',
                    source=ProductSourceTypeChoices.MANUAL,
                ),
            ),
            _build_link(
                request,
                key='all_products',
                label='همه محصولات',
                url=reverse('products:list'),
            ),
            *(
                [
                    _build_link(
                        request,
                        key='dashboard_products',
                        label='داشبورد محصولات',
                        url=reverse('dashboard'),
                    ),
                ]
                if user.is_superuser
                else []
            ),
            *quick_links,
        ]
        if user.is_superuser and user.has_perm('products.review_product'):
            quick_links.insert(
                2,
                _build_link(
                    request,
                    key='rejected_products',
                    label='رد شده',
                    url=build_url(
                        'products:list',
                        status=ProductStatusChoices.REJECTED,
                    ),
                ),
            )
        if user.has_perm('accounts.view_operator_dashboard'):
            quick_links.append(_build_link(
                request,
                key='operator_dashboard',
                label='داشبورد اپراتور',
                url=reverse('operator_dashboard'),
            ))
    elif user.has_perm('products.view_product'):
        quick_links.insert(
            0,
            _build_link(
                request,
                key='manual_products',
                label='محصولات دستی',
                url=build_url(
                    'products:list',
                    source=ProductSourceTypeChoices.MANUAL,
                ),
                variant='primary',
            ),
        )
        quick_links.insert(
            0,
            _build_link(
                request,
                key='all_products',
                label='همه محصولات',
                url=reverse('products:list'),
                variant='primary',
            ),
        )

    return quick_links
