from django.db.models.signals import m2m_changed, post_migrate
from django.dispatch import receiver

from .constants import ROLE_NAME_SET
from .models import User
from .services import ensure_default_roles


@receiver(post_migrate)
def sync_default_roles(sender, **kwargs):
    if sender.name == 'accounts':
        ensure_default_roles()


@receiver(m2m_changed, sender=User.groups.through)
def sync_user_access_flags(sender, instance, action, reverse, model, pk_set, **kwargs):
    if reverse or action not in {'post_add', 'post_remove', 'post_clear'}:
        return

    if pk_set and not model.objects.filter(pk__in=pk_set, name__in=ROLE_NAME_SET).exists():
        return

    instance.sync_access_flags()
