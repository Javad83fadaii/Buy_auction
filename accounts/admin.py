from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.contrib.admin.sites import NotRegistered
from django.utils.translation import gettext_lazy as _

from .constants import ROLE_NAME_SET
from .forms import UserAdminChangeForm, UserAdminCreationForm
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = UserAdminCreationForm
    form = UserAdminChangeForm
    model = User
    ordering = ('-created_at',)
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'primary_role',
        'is_active',
        'is_staff',
        'created_at',
    )
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'groups', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    readonly_fields = ('created_at', 'updated_at', 'last_login')
    filter_horizontal = ()

    fieldsets = (
        (_('اطلاعات ورود'), {'fields': ('username', 'password')}),
        (_('اطلاعات شخصی'), {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        (
            _('دسترسی‌ها'),
            {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions', 'role')},
        ),
        (_('زمان‌ها'), {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (
            _('ایجاد کاربر'),
            {
                'classes': ('wide',),
                'fields': (
                    'username',
                    'email',
                    'first_name',
                    'last_name',
                    'phone_number',
                    'is_active',
                    'role',
                    'password1',
                    'password2',
                ),
            },
        ),
    )

    actions = ('activate_users', 'deactivate_users')

    @admin.display(description='نقش')
    def primary_role(self, obj):
        return obj.role_display

    @admin.action(description='فعال‌سازی کاربران انتخاب‌شده')
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='غیرفعال‌سازی کاربران انتخاب‌شده')
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)

class GroupAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.name in ROLE_NAME_SET:
            return False
        return super().has_delete_permission(request, obj)


try:
    admin.site.unregister(Group)
except NotRegistered:
    pass

admin.site.register(Group, GroupAdmin)
