from urllib.parse import urlencode

from django.urls import reverse

from products.choices import ProductSourceTypeChoices, ProductStatusChoices


def build_url(view_name: str, **params) -> str:
    base_url = reverse(view_name)
    filtered_params = {key: value for key, value in params.items() if value not in (None, '', [])}
    if not filtered_params:
        return base_url
    return f'{base_url}?{urlencode(filtered_params)}'


def build_quick_links(user) -> list[dict[str, str]]:
    """Quick navigation links shared by the dashboard sidebar across all pages."""
    if not user.is_authenticated:
        return []

    quick_links = [
        {
            'label': 'تغییر رمز',
            'url': reverse('accounts:change_password'),
            'variant': 'secondary',
        },
    ]

    if user.has_perm('products.add_product'):
        quick_links = [
            {
                'label': 'داشبورد',
                'url': reverse('products:dashboard'),
                'variant': 'primary',

            },
             {
                'label': 'لیست حراجی‌ها',
                'url': reverse('products:auction_list'),
                'variant': 'primary',
            },
            {
                'label': 'ثبت محصول',
                'url': reverse('products:create'),
                'variant': 'secondary',
            },
            
            {
                'label': 'همه محصولات',
                'url': reverse('products:list'),
                'variant': 'secondary',
            },
            {
                'label': 'داشبورد محصولات',
                'url': reverse('products:dashboard'),
                'variant': 'secondary',
            },
            *quick_links,
        ]
        if user.has_perm('products.review_product'):
            quick_links.insert(
                2,
                {
                    'label': 'در انتظار بررسی',
                    'url': build_url(
                        'products:list',
                        status=ProductStatusChoices.PENDING_REVIEW,
                    ),
                    'variant': 'secondary',
                },
            )
        if user.has_perm('accounts.view_operator_dashboard'):
            quick_links.append(
                {
                    'label': 'داشبورد اپراتور',
                    'url': reverse('operator_dashboard'),
                    'variant': 'secondary',
                }
            )
    elif user.has_perm('products.view_product'):
        quick_links.insert(
            0,
            {
                'label': 'همه محصولات',
                'url': reverse('products:list'),
                'variant': 'primary',
            },
        )

    return quick_links
