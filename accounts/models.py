from django.contrib.auth.models import AbstractUser, Group
from django.db import models

from .constants import ADMIN_ROLE, ROLE_NAME_SET, get_role_title
from .managers import CustomUserManager


class User(AbstractUser):
    phone_number = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'
        permissions = [
            ('view_dashboard', 'Can view dashboard'),
            ('view_operator_dashboard', 'Can view operator dashboard'),
            ('view_viewer_dashboard', 'Can view viewer dashboard'),
        ]

    def __str__(self) -> str:
        return self.get_full_name() or self.username

    @property
    def roles(self) -> list[str]:
        return list(
            self.groups.filter(name__in=ROLE_NAME_SET)
            .order_by('name')
            .values_list('name', flat=True)
        )

    @property
    def primary_role(self) -> str:
        return self.roles[0] if self.roles else ''

    @property
    def primary_role_title(self) -> str:
        return get_role_title(self.primary_role)

    @property
    def role_display(self) -> str:
        return ', '.join(get_role_title(role_name) for role_name in self.roles) or '-'

    def has_role(self, role_name: str) -> bool:
        return self.groups.filter(name=role_name).exists()

    def set_role(self, group: Group | None) -> None:
        role_groups = Group.objects.filter(name__in=ROLE_NAME_SET)
        self.groups.remove(*role_groups)
        if group is not None:
            self.groups.add(group)
        self.sync_access_flags()

    def sync_access_flags(self) -> None:
        expected_is_staff = self.is_superuser or self.has_role(ADMIN_ROLE)
        if self.is_staff == expected_is_staff:
            return

        self.is_staff = expected_is_staff
        self.save(update_fields=['is_staff', 'updated_at'])
