from orders.models import Cart


def cart_processor(request):
    """
    Context processor للسلة - يضيف معلومات السلة لجميع الصفحات
    """
    if request.user.is_authenticated:
        try:
            cart = request.user.cart
            cart_items = cart.items.all().select_related('product', 'variant')
            cart_total = cart.get_total_price()
            cart_count = cart.get_total_items()
        except Cart.DoesNotExist:
            cart = None
            cart_items = []
            cart_total = 0
            cart_count = 0
    else:
        # للمستخدمين غير المسجلين، السلة تكون فارغة هنا
        # البيانات تأتي من JavaScript/localStorage
        cart = None
        cart_items = []
        cart_total = 0
        cart_count = 0

    return {
        'cart': cart,
        'cart_items': cart_items,
        'cart_total': cart_total,
        'cart_count': cart_count,
    }