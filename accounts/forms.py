from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm, UserCreationForm
from django.contrib.auth.models import Group

from .constants import ROLE_NAME_SET

User = get_user_model()


def get_role_queryset():
    return Group.objects.filter(name__in=ROLE_NAME_SET).order_by('name')


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='نام کاربری',
        widget=forms.TextInput(attrs={'autofocus': True, 'placeholder': 'نام کاربری'}),
    )
    password = forms.CharField(
        label='رمز عبور',
        strip=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'رمز عبور'}),
    )

    error_messages = {
        'invalid_login': 'نام کاربری یا رمز عبور صحیح نیست.',
        'inactive': 'این حساب کاربری غیرفعال است.',
    }


class RoleAdminMixin(forms.ModelForm):
    role = forms.ModelChoiceField(
        label='نقش',
        queryset=Group.objects.none(),
        required=False,
        empty_label='بدون نقش',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].queryset = get_role_queryset()

        if self.instance.pk:
            self.fields['role'].initial = (
                self.instance.groups.filter(name__in=ROLE_NAME_SET).order_by('name').first()
            )

    def save(self, commit=True):
        user = super().save(commit=commit)
        role = self.cleaned_data.get('role')
        pending_save_m2m = getattr(self, 'save_m2m', None)

        def apply_role():
            if callable(pending_save_m2m):
                pending_save_m2m()
            user.set_role(role)

        if commit:
            apply_role()
        else:
            self.save_m2m = apply_role  # type: ignore[method-assign]

        return user


class UserAdminCreationForm(RoleAdminMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'is_active', 'role')


class UserAdminChangeForm(RoleAdminMixin, UserChangeForm):
    password = None

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'is_active',
            'is_staff',
            'is_superuser',
            'role',
        )
