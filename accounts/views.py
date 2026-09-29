from urllib.parse import urlencode, urlsplit

from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeDoneView, PasswordChangeView
from django.db.models import Count, Q
from django.urls import Resolver404, resolve, reverse, reverse_lazy
from django.views.generic import TemplateView

from .constants import EXPERT_ROLE
from .forms import LoginForm
from .permissions import RolePermissionMixin
from products.choices import AuctionStatusChoices, ProductSourceTypeChoices, ProductStatusChoices
from products.models import Auction, Product


EXPERT_ALLOWED_REDIRECTS = {
    'products:list',
    'products:detail',
    'accounts:change_password',
    'accounts:change_password_done',
    'accounts:logout',
}


def get_user_default_url(user) -> str:
    if user.has_role(EXPERT_ROLE) and user.has_perm('products.view_product'):
        return reverse('products:list')
    return reverse('dashboard')


def resolve_redirect_view_name(redirect_url: str) -> str:
    try:
        return resolve(urlsplit(redirect_url).path).view_name
    except Resolver404:
        return ''


class UserLoginView(LoginView):
    template_name = 'accounts/login.html'
    form_class = LoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        redirect_url = self.get_redirect_url()

        if user.has_role(EXPERT_ROLE):
            if redirect_url and resolve_redirect_view_name(redirect_url) in EXPERT_ALLOWED_REDIRECTS:
                return redirect_url
            return reverse('products:list')

        if redirect_url:
            return redirect_url
        return super().get_success_url()


class UserLogoutView(LogoutView):
    next_page = reverse_lazy('accounts:login')
    http_method_names = ['post']


class UserPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/change_password.html'
    success_url = reverse_lazy('accounts:change_password_done')


class UserPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = 'accounts/change_password_done.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['back_url'] = get_user_default_url(self.request.user)
        context['back_label'] = (
            'بازگشت به لیست محصولات'
            if self.request.user.has_role(EXPERT_ROLE)
            else 'بازگشت به داشبورد'
        )
        return context


class DashboardView(RolePermissionMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'
    permission_required = 'accounts.view_dashboard'

    def _build_url(self, view_name: str, **params) -> str:
        base_url = reverse(view_name)
        filtered_params = {key: value for key, value in params.items() if value not in (None, '', [])}
        if not filtered_params:
            return base_url
        query_string = urlencode(filtered_params)
        return f'{base_url}?{query_string}'

    def get_product_stats(self) -> dict[str, int]:
        return Product.objects.aggregate(
            total_products=Count('id'),
            manual_products=Count(
                'id',
                filter=Q(source_type=ProductSourceTypeChoices.MANUAL),
            ),
            auction_products=Count(
                'id',
                filter=~Q(source_type=ProductSourceTypeChoices.MANUAL),
            ),
            pending_review_products=Count(
                'id',
                filter=Q(status=ProductStatusChoices.PENDING_REVIEW),
            ),
            to_buy_products=Count(
                'id',
                filter=Q(to_buy=True),
            ),
            cancelled_products=Count(
                'id',
                filter=Q(is_cancelled=True),
            ),
        )

    def get_auction_stats(self) -> dict[str, int]:
        return Auction.objects.aggregate(
            total_auctions=Count('id'),
            ongoing_auctions=Count(
                'id',
                filter=Q(status=AuctionStatusChoices.ONGOING),
            ),
            upcoming_auctions=Count(
                'id',
                filter=Q(status=AuctionStatusChoices.UPCOMING),
            ),
            ended_auctions=Count(
                'id',
                filter=Q(status=AuctionStatusChoices.ENDED),
            ),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        can_view_operator_dashboard = self.request.user.has_perm(
            'accounts.view_operator_dashboard'
        )
        can_manage_products = self.request.user.has_perm('products.add_product')
        can_review_products = self.request.user.has_perm('products.review_product')
        product_stats = self.get_product_stats() if can_manage_products else {}
        auction_stats = self.get_auction_stats() if can_manage_products else {}

        context['can_view_operator_dashboard'] = can_view_operator_dashboard
        context['can_manage_products'] = can_manage_products
        context['can_review_products'] = can_review_products
        context['product_stats'] = product_stats
        context['auction_stats'] = auction_stats
        context['manual_products'] = (
            Product.objects.filter(source_type=ProductSourceTypeChoices.MANUAL)
            .select_related('auction')
            .order_by('-created_at', '-pk')[:6]
            if can_manage_products
            else []
        )
        context['all_products'] = (
            Product.objects.select_related('auction')
            .order_by('-created_at', '-pk')[:6]
            if can_manage_products
            else []
        )
        context['auction_items'] = (
            Auction.objects.order_by('-start_date', '-created_at')[:6]
            if can_manage_products
            else []
        )
        quick_links = [
            {
                'label': 'تغییر رمز',
                'url': reverse('accounts:change_password'),
                'variant': 'secondary',
            },
        ]
        if can_manage_products:
            quick_links = [
                {
                    'label': 'لیست حراجی‌ها',
                    'url': reverse('products:auction_list'),
                    'variant': 'primary',
                },
                {
                    'label': 'ثبت محصول',
                    'url': reverse('products:create'),
                    'variant': 'primary',
                },
                {
                    'label': 'همه محصولات',
                    'url': reverse('products:list'),
                    'variant': 'secondary',
                },
                {
                    'label': 'ثبت دستی',
                    'url': self._build_url(
                        'products:list',
                        source=ProductSourceTypeChoices.MANUAL,
                    ),
                    'variant': 'secondary',
                },
                {
                    'label': 'داشبورد محصولات',
                    'url': reverse('products:dashboard'),
                    'variant': 'secondary',
                },
                *quick_links,
            ]
        if can_review_products:
            quick_links.insert(
                2,
                {
                    'label': 'در انتظار بررسی',
                    'url': self._build_url(
                        'products:list',
                        status=ProductStatusChoices.PENDING_REVIEW,
                    ),
                    'variant': 'secondary',
                },
            )
        if can_view_operator_dashboard:
            quick_links.append(
                {
                    'label': 'داشبورد اپراتور',
                    'url': reverse('operator_dashboard'),
                    'variant': 'secondary',
                }
            )
        context['quick_links'] = quick_links
        context['manual_products_url'] = self._build_url(
            'products:list',
            source=ProductSourceTypeChoices.MANUAL,
        )
        context['auction_products_url'] = reverse('products:auction_list')
        context['all_products_url'] = reverse('products:list')
        context['pending_review_url'] = self._build_url(
            'products:list',
            status=ProductStatusChoices.PENDING_REVIEW,
        )
        return context


class OperatorDashboardView(RolePermissionMixin, TemplateView):
    template_name = 'dashboard/operator_dashboard.html'
    permission_required = 'accounts.view_operator_dashboard'

    def handle_no_permission(self):
        return super().handle_no_permission()
