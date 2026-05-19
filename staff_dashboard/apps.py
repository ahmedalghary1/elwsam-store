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
    from .permissions import get_order_editor_group

    get_order_editor_group()
