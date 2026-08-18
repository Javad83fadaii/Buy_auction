from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin


class ActiveUserRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_active:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class RolePermissionMixin(ActiveUserRequiredMixin, PermissionRequiredMixin):
    raise_exception = False
