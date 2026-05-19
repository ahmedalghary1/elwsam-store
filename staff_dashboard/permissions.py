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
