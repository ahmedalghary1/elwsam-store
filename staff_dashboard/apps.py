from django.apps import AppConfig
from django.db.models.signals import post_migrate


class StaffDashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "staff_dashboard"
    verbose_name = "لوحة تحكم الوسام"

    def ready(self):
        post_migrate.connect(
            ensure_order_editor_group,
            sender=self,
            dispatch_uid="staff_dashboard.ensure_order_editor_group",
        )


def ensure_order_editor_group(**kwargs):
    from django.contrib.auth.models import Group, Permission

    from .permissions import ORDER_EDITOR_GROUP_NAME, ORDER_EDITOR_PERMISSION_CODENAMES

    permissions = Permission.objects.filter(
        content_type__app_label="orders",
        codename__in=ORDER_EDITOR_PERMISSION_CODENAMES,
    )
    if permissions.count() != len(ORDER_EDITOR_PERMISSION_CODENAMES):
        return

    group, _created = Group.objects.get_or_create(name=ORDER_EDITOR_GROUP_NAME)
    group.permissions.add(*permissions)
