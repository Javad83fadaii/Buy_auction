import logging

from django.contrib import messages
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.urls import reverse_lazy
from django.views.generic import FormView

from accounts.permissions import RolePermissionMixin

from .forms import ProductCreateForm
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
