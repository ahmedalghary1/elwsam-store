# def wishlist_processor(request):
#     """
#     Context processor للمفضلة - يضيف معلومات المفضلة لجميع الصفحات
#     """
#     if request.user.is_authenticated:
#         wishlist_items = request.user.wishlist.all().select_related('product')
#         wishlist_count = wishlist_items.count()
#     else:
#         # للمستخدمين غير المسجلين، المفضلة تكون فارغة هنا
#         # البيانات تأتي من JavaScript/localStorage
#         wishlist_items = []
#         wishlist_count = 0

#     return {
#         'wishlist_items': wishlist_items,
#         'wishlist_count': wishlist_count,
#     }