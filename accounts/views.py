from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeDoneView, PasswordChangeView
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .forms import LoginForm
from .permissions import RolePermissionMixin


class UserLoginView(LoginView):
    template_name = 'accounts/login.html'
    form_class = LoginForm
    redirect_authenticated_user = True


class UserLogoutView(LogoutView):
    next_page = reverse_lazy('accounts:login')
    http_method_names = ['post']


class UserPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/change_password.html'
    success_url = reverse_lazy('accounts:change_password_done')


class UserPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = 'accounts/change_password_done.html'


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
