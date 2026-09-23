from dataclasses import dataclass

from django.contrib.auth.models import Group, Permission
from django.db import transaction

from .constants import ADMIN_ROLE, EXPERT_ROLE, MANAGER_ROLE, OPERATOR_ROLE, ROLE_DEFINITIONS


@dataclass(frozen=True)
class PermissionBlueprint:
    app_label: str
    model: str | None = None
    codenames: tuple[str, ...] = ()


ROLE_PERMISSION_BLUEPRINTS = {
    ADMIN_ROLE: (
        PermissionBlueprint(app_label='accounts'),
        PermissionBlueprint(app_label='products'),
        PermissionBlueprint(app_label='auth', model='group'),
    ),
    MANAGER_ROLE: (
        PermissionBlueprint(
            app_label='accounts',
            codenames=('view_dashboard',),
        ),
        PermissionBlueprint(
            app_label='products',
            codenames=(
                'add_product',
                'change_product',
                'view_product',
                'review_product',
                'add_auction',
                'change_auction',
                'view_auction',
            ),
        ),
    ),
    OPERATOR_ROLE: (
        PermissionBlueprint(
            app_label='accounts',
            codenames=('view_dashboard', 'view_operator_dashboard'),
        ),
        PermissionBlueprint(
            app_label='products',
            codenames=(
                'add_product',
                'change_product',
                'view_product',
                'add_auction',
                'change_auction',
                'view_auction',
            ),
        ),
    ),
    EXPERT_ROLE: (
        PermissionBlueprint(
            app_label='products',
            codenames=('view_product', 'view_auction'),
        ),
    ),
}


def resolve_role_permissions(role_name: str) -> list[Permission]:
    permissions: list[Permission] = []

    for blueprint in ROLE_PERMISSION_BLUEPRINTS.get(role_name, ()):
        queryset = Permission.objects.filter(content_type__app_label=blueprint.app_label)

        if blueprint.model:
            queryset = queryset.filter(content_type__model=blueprint.model)

        if blueprint.codenames:
            queryset = queryset.filter(codename__in=blueprint.codenames)

        permissions.extend(queryset)

    return permissions


@transaction.atomic
def ensure_default_roles() -> None:
    for role_name in ROLE_PERMISSION_BLUEPRINTS:
        group, _ = Group.objects.get_or_create(name=role_name)
        permissions = resolve_role_permissions(role_name)
        group.permissions.set(permissions)
    Group.objects.filter(name='VIEWER').delete()
