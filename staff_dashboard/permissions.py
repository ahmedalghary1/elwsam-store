ORDER_EDITOR_GROUP_NAME = "Order Editors"
ORDER_EDITOR_PERMISSION_CODENAMES = ("view_order", "change_order")
ORDER_EDITOR_PERMISSIONS = tuple(f"orders.{codename}" for codename in ORDER_EDITOR_PERMISSION_CODENAMES)


def has_order_editor_access(user):
    if not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    return user.is_active and user.is_staff and user.has_perms(ORDER_EDITOR_PERMISSIONS)


def can_manage_full_dashboard(user):
    return getattr(user, "is_authenticated", False) and user.is_superuser


def get_order_editor_group():
    from django.contrib.auth.models import Group, Permission

    group, _created = Group.objects.get_or_create(name=ORDER_EDITOR_GROUP_NAME)
    permissions = Permission.objects.filter(
        content_type__app_label="orders",
        codename__in=ORDER_EDITOR_PERMISSION_CODENAMES,
    )
    if permissions.count() == len(ORDER_EDITOR_PERMISSION_CODENAMES):
        group.permissions.add(*permissions)
    return group


def set_order_editor_role(user, enabled):
    from django.contrib.auth.models import Permission

    group = get_order_editor_group()
    permissions = Permission.objects.filter(
        content_type__app_label="orders",
        codename__in=ORDER_EDITOR_PERMISSION_CODENAMES,
    )
    if enabled:
        user.groups.add(group)
        user.user_permissions.add(*permissions)
    else:
        user.groups.remove(group)
        user.user_permissions.remove(*permissions)
