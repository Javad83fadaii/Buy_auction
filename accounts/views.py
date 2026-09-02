from urllib.parse import urlsplit

from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeDoneView, PasswordChangeView
from django.urls import Resolver404, resolve, reverse, reverse_lazy
from django.views.generic import TemplateView

from .constants import VIEWER_ROLE
from .forms import LoginForm
from .permissions import RolePermissionMixin


VIEWER_ALLOWED_REDIRECTS = {
    'products:list',
    'products:detail',
    'accounts:change_password',
    'accounts:change_password_done',
    'accounts:logout',
}


def get_user_default_url(user) -> str:
    if user.has_role(VIEWER_ROLE) and user.has_perm('products.view_product'):
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

        if user.has_role(VIEWER_ROLE):
            if redirect_url and resolve_redirect_view_name(redirect_url) in VIEWER_ALLOWED_REDIRECTS:
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
            if self.request.user.has_role(VIEWER_ROLE)
            else 'بازگشت به داشبورد'
        )
        return context


class DashboardView(RolePermissionMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'
    permission_required = 'accounts.view_dashboard'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_view_operator_dashboard'] = self.request.user.has_perm(
            'accounts.view_operator_dashboard'
        )
        context['can_view_viewer_dashboard'] = self.request.user.has_perm(
            'accounts.view_viewer_dashboard'
        )
        context['can_manage_products'] = self.request.user.has_perm('products.add_product')
        return context


class OperatorDashboardView(RolePermissionMixin, TemplateView):
    template_name = 'dashboard/operator_dashboard.html'
    permission_required = 'accounts.view_operator_dashboard'

    def handle_no_permission(self):
        return super().handle_no_permission()
