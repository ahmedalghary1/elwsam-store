from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import redirect_to_login
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from orders.models import Cart, Order, OrderItem
from products.models import (
    Category,
    HomeProductCollectionItem,
    Product,
    ProductColor,
    ProductType,
    ProductTypeColor,
    ProductTypeImage,
    ProductVariant,
)

from .forms import (
    CategoryForm,
    CustomerForm,
    HomeCollectionItemForm,
    OrderStatusForm,
    ProductColorForm,
    ProductForm,
    ProductTypeColorForm,
    ProductTypeDashboardForm,
    ProductTypeImageForm,
)


ORDER_STATUS_META = {
    "pending": ("قيد المراجعة", "warning"),
    "paid": ("مدفوع", "success"),
    "processing": ("قيد التجهيز", "info"),
    "shipped": ("تم الشحن", "primary"),
    "delivered": ("تم التسليم", "success"),
    "cancelled": ("ملغي", "danger"),
}


def superuser_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), reverse("accounts:login"))
        if not request.user.is_superuser:
            messages.error(request, "هذه اللوحة مخصصة للمشرف العام فقط.")
            return redirect("index")
        return view_func(request, *args, **kwargs)

    return wrapped


def _render(request, template_name, context):
    context.setdefault("active_nav", "dashboard")
    try:
        context.setdefault("django_admin_url", reverse("admin:index"))
    except NoReverseMatch:
        context.setdefault("django_admin_url", "/admin/")
    return render(request, template_name, context)


def _paginate(request, queryset, per_page=20):
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get("page"))


def _admin_change_url(obj):
    try:
        return reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change", args=[obj.pk])
    except NoReverseMatch:
        return ""


def _status_context():
    return [
        {
            "value": value,
            "label": ORDER_STATUS_META.get(value, (label, "muted"))[0],
            "tone": ORDER_STATUS_META.get(value, (label, "muted"))[1],
        }
        for value, label in Order.STATUS_CHOICES
    ]


def _product_management_context(product):
    if not product:
        return {}
    return {
        "product_management": True,
        "product": product,
        "product_colors": ProductColor.objects.filter(product=product).select_related("color").order_by("order", "id"),
        "product_types": ProductType.objects.filter(product=product)
        .select_related("type")
        .prefetch_related("type_colors__color", "type_images__color")
        .order_by("order", "id"),
        "product_color_form": ProductColorForm(product=product),
        "product_color_add_url": reverse("staff_dashboard:product_color_add", args=[product.pk]),
        "product_type_add_url": reverse("staff_dashboard:product_type_add", args=[product.pk]),
    }


@superuser_required
def dashboard(request):
    today = timezone.localdate()
    since_30_days = timezone.now() - timezone.timedelta(days=30)

    order_status_counts = {
        row["status"]: row["count"]
        for row in Order.objects.values("status").annotate(count=Count("id"))
    }
    status_cards = [
        {
            "value": value,
            "label": ORDER_STATUS_META.get(value, (label, "muted"))[0],
            "tone": ORDER_STATUS_META.get(value, (label, "muted"))[1],
            "count": order_status_counts.get(value, 0),
        }
        for value, label in Order.STATUS_CHOICES
    ]

    revenue_30_days = (
        Order.objects.exclude(status="cancelled")
        .filter(created_at__gte=since_30_days)
        .aggregate(total=Sum("total_price"))["total"]
        or 0
    )
    orders_today = Order.objects.filter(created_at__date=today).count()
    active_products = Product.objects.filter(is_active=True).count()
    inactive_products = Product.objects.filter(is_active=False).count()

    home_collection_counts = {
        row["collection_type"]: row["count"]
        for row in HomeProductCollectionItem.objects.filter(is_active=True)
        .values("collection_type")
        .annotate(count=Count("id"))
    }
    collection_labels = dict(HomeProductCollectionItem.COLLECTION_CHOICES)

    latest_orders = (
        Order.objects.select_related("user")
        .prefetch_related("items")
        .order_by("-created_at")[:8]
    )
    simple_low_stock = Product.objects.filter(is_active=True, stock__lte=5).order_by("stock", "name")[:6]
    variant_low_stock = (
        ProductVariant.objects.filter(stock__lte=5)
        .select_related("product", "pattern", "color", "size")
        .order_by("stock", "product__name")[:6]
    )

    context = {
        "active_nav": "dashboard",
        "stats": [
            {"label": "المنتجات النشطة", "value": active_products, "icon": "fa-box", "tone": "primary"},
            {"label": "منتجات مخفية", "value": inactive_products, "icon": "fa-eye-slash", "tone": "muted"},
            {"label": "طلبات اليوم", "value": orders_today, "icon": "fa-receipt", "tone": "info"},
            {"label": "مبيعات آخر 30 يوم", "value": f"{revenue_30_days} ج.م", "icon": "fa-chart-line", "tone": "success"},
        ],
        "status_cards": status_cards,
        "latest_orders": latest_orders,
        "simple_low_stock": simple_low_stock,
        "variant_low_stock": variant_low_stock,
        "collection_cards": [
            {
                "value": key,
                "label": collection_labels.get(key, key),
                "count": home_collection_counts.get(key, 0),
            }
            for key, _label in HomeProductCollectionItem.COLLECTION_CHOICES
        ],
        "totals": {
            "categories": Category.objects.count(),
            "customers": get_user_model().objects.filter(is_superuser=False).count(),
            "carts": Cart.objects.count(),
        },
    }
    return _render(request, "staff_dashboard/dashboard.html", context)


@superuser_required
def products_list(request):
    queryset = Product.objects.select_related("category").prefetch_related("images").order_by("-updated_at")
    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "")
    status = request.GET.get("status", "all")

    if query:
        queryset = queryset.filter(
            Q(name__icontains=query)
            | Q(slug__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
        )
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    if status == "active":
        queryset = queryset.filter(is_active=True)
    elif status == "inactive":
        queryset = queryset.filter(is_active=False)

    page_obj = _paginate(request, queryset, per_page=18)
    return _render(
        request,
        "staff_dashboard/products_list.html",
        {
            "active_nav": "products",
            "page_obj": page_obj,
            "products": page_obj.object_list,
            "categories": Category.objects.order_by("order", "name"),
            "filters": {"q": query, "category": category_id, "status": status},
            "total_count": queryset.count(),
        },
    )


@superuser_required
def product_form(request, pk=None):
    product = get_object_or_404(Product, pk=pk) if pk else None
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            saved_product = form.save()
            messages.success(request, "تم حفظ المنتج بنجاح.")
            return redirect("staff_dashboard:product_edit", pk=saved_product.pk)
        messages.error(request, "يرجى مراجعة الحقول المحددة ثم المحاولة مرة أخرى.")
    else:
        form = ProductForm(instance=product)

    context = {
            "active_nav": "products",
            "form": form,
            "page_title": "تعديل منتج" if product else "إضافة منتج",
            "page_subtitle": (
                "بيانات المنتج الأساسية. بعد حفظ المنتج ستظهر إدارة الألوان والأنواع وتفاصيل كل نوع هنا."
                if not product
                else "بيانات المنتج الأساسية مع إدارة الألوان والأنواع المرتبطة به."
            ),
            "cancel_url": reverse("staff_dashboard:products"),
            "delete_url": reverse("staff_dashboard:product_delete", args=[product.pk]) if product else "",
            "advanced_url": _admin_change_url(product) if product else "",
            "advanced_label": "تعديل متقدم في Django Admin",
            "multipart": True,
        }
    context.update(_product_management_context(product))
    return _render(request, "staff_dashboard/form.html", context)


@superuser_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        if OrderItem.objects.filter(product=product).exists():
            product.is_active = False
            product.save(update_fields=["is_active", "updated_at"])
            messages.warning(request, "تم إخفاء المنتج بدل حذفه لأنه مرتبط بطلبات سابقة.")
        else:
            product.delete()
            messages.success(request, "تم حذف المنتج بنجاح.")
        return redirect("staff_dashboard:products")

    return _render(
        request,
        "staff_dashboard/confirm_delete.html",
        {
            "active_nav": "products",
            "object_name": product.name,
            "object_type": "منتج",
            "cancel_url": reverse("staff_dashboard:products"),
            "warning": "إذا كان المنتج مرتبطًا بطلبات سابقة سيتم إخفاؤه بدل حذفه حفاظًا على سجل الطلبات.",
        },
    )


@superuser_required
def product_color_add(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method != "POST":
        return redirect("staff_dashboard:product_edit", pk=product.pk)

    form = ProductColorForm(request.POST, product=product)
    if form.is_valid():
        form.save()
        if not product.has_colors:
            product.has_colors = True
            product.save(update_fields=["has_colors", "updated_at"])
        messages.success(request, "تم ربط اللون بالمنتج بنجاح.")
    else:
        messages.error(request, "تعذر إضافة اللون. تأكد من اختيار لون أو كتابة لون جديد غير مكرر.")
    return redirect("staff_dashboard:product_edit", pk=product.pk)


@superuser_required
def product_color_delete(request, pk, color_pk):
    product = get_object_or_404(Product, pk=pk)
    product_color = get_object_or_404(ProductColor, pk=color_pk, product=product)
    if request.method == "POST":
        color_name = product_color.color.name
        product_color.delete()
        if not ProductColor.objects.filter(product=product).exists() and product.has_colors:
            product.has_colors = False
            product.save(update_fields=["has_colors", "updated_at"])
        messages.success(request, f"تم حذف لون {color_name} من المنتج.")
    return redirect("staff_dashboard:product_edit", pk=product.pk)


@superuser_required
def product_type_form(request, product_pk, type_pk=None):
    product = get_object_or_404(Product, pk=product_pk)
    product_type = get_object_or_404(ProductType, pk=type_pk, product=product) if type_pk else None

    if request.method == "POST":
        form = ProductTypeDashboardForm(request.POST, request.FILES, instance=product_type, product=product)
        if form.is_valid():
            saved_type = form.save()
            messages.success(request, "تم حفظ نوع المنتج بنجاح.")
            return redirect("staff_dashboard:product_type_edit", product_pk=product.pk, type_pk=saved_type.pk)
        messages.error(request, "يرجى مراجعة بيانات النوع.")
    else:
        form = ProductTypeDashboardForm(instance=product_type, product=product)

    context = {
        "active_nav": "products",
        "product": product,
        "product_type": product_type,
        "form": form,
        "type_colors": ProductTypeColor.objects.filter(product_type=product_type).select_related("color").order_by("order", "id") if product_type else [],
        "type_images": ProductTypeImage.objects.filter(product_type=product_type).select_related("color").order_by("order", "id") if product_type else [],
        "type_color_form": ProductTypeColorForm(product_type=product_type) if product_type else None,
        "type_image_form": ProductTypeImageForm(product_type=product_type) if product_type else None,
        "cancel_url": reverse("staff_dashboard:product_edit", args=[product.pk]),
        "delete_url": reverse("staff_dashboard:product_type_delete", args=[product.pk, product_type.pk]) if product_type else "",
        "advanced_url": _admin_change_url(product_type) if product_type else "",
        "page_title": "تعديل نوع المنتج" if product_type else "إضافة نوع للمنتج",
        "multipart": True,
    }
    return _render(request, "staff_dashboard/product_type_form.html", context)


@superuser_required
def product_type_delete(request, product_pk, type_pk):
    product = get_object_or_404(Product, pk=product_pk)
    product_type = get_object_or_404(ProductType, pk=type_pk, product=product)
    if request.method == "POST":
        type_name = product_type.type.name
        product_type.delete()
        messages.success(request, f"تم حذف نوع {type_name} من المنتج.")
        return redirect("staff_dashboard:product_edit", pk=product.pk)

    return _render(
        request,
        "staff_dashboard/confirm_delete.html",
        {
            "active_nav": "products",
            "object_name": str(product_type),
            "object_type": "نوع منتج",
            "cancel_url": reverse("staff_dashboard:product_type_edit", args=[product.pk, product_type.pk]),
            "warning": "سيتم حذف تفاصيل هذا النوع وألوانه وصوره من هذا المنتج فقط.",
        },
    )


@superuser_required
def product_type_color_add(request, type_pk):
    product_type = get_object_or_404(ProductType.objects.select_related("product"), pk=type_pk)
    if request.method != "POST":
        return redirect("staff_dashboard:product_type_edit", product_pk=product_type.product_id, type_pk=product_type.pk)

    form = ProductTypeColorForm(request.POST, product_type=product_type)
    if form.is_valid():
        form.save()
        messages.success(request, "تم ربط اللون بهذا النوع بنجاح.")
    else:
        messages.error(request, "تعذر إضافة اللون لهذا النوع. تأكد من أن اللون غير مكرر.")
    return redirect("staff_dashboard:product_type_edit", product_pk=product_type.product_id, type_pk=product_type.pk)


@superuser_required
def product_type_color_delete(request, type_pk, color_pk):
    product_type = get_object_or_404(ProductType.objects.select_related("product"), pk=type_pk)
    type_color = get_object_or_404(ProductTypeColor, pk=color_pk, product_type=product_type)
    if request.method == "POST":
        color_name = type_color.color.name
        type_color.delete()
        messages.success(request, f"تم حذف لون {color_name} من هذا النوع.")
    return redirect("staff_dashboard:product_type_edit", product_pk=product_type.product_id, type_pk=product_type.pk)


@superuser_required
def product_type_image_add(request, type_pk):
    product_type = get_object_or_404(ProductType.objects.select_related("product"), pk=type_pk)
    if request.method != "POST":
        return redirect("staff_dashboard:product_type_edit", product_pk=product_type.product_id, type_pk=product_type.pk)

    form = ProductTypeImageForm(request.POST, request.FILES, product_type=product_type)
    if form.is_valid():
        form.save()
        messages.success(request, "تم إضافة صورة النوع بنجاح.")
    else:
        messages.error(request, "تعذر إضافة الصورة. تأكد من اختيار ملف صورة صالح.")
    return redirect("staff_dashboard:product_type_edit", product_pk=product_type.product_id, type_pk=product_type.pk)


@superuser_required
def product_type_image_delete(request, type_pk, image_pk):
    product_type = get_object_or_404(ProductType.objects.select_related("product"), pk=type_pk)
    type_image = get_object_or_404(ProductTypeImage, pk=image_pk, product_type=product_type)
    if request.method == "POST":
        type_image.delete()
        messages.success(request, "تم حذف صورة النوع.")
    return redirect("staff_dashboard:product_type_edit", product_pk=product_type.product_id, type_pk=product_type.pk)


@superuser_required
def categories_list(request):
    queryset = Category.objects.annotate(products_count=Count("product")).order_by("order", "name")
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "all")

    if query:
        queryset = queryset.filter(Q(name__icontains=query) | Q(slug__icontains=query))
    if status == "active":
        queryset = queryset.filter(is_active=True)
    elif status == "inactive":
        queryset = queryset.filter(is_active=False)

    page_obj = _paginate(request, queryset, per_page=18)
    return _render(
        request,
        "staff_dashboard/categories_list.html",
        {
            "active_nav": "categories",
            "page_obj": page_obj,
            "categories": page_obj.object_list,
            "filters": {"q": query, "status": status},
            "total_count": queryset.count(),
        },
    )


@superuser_required
def category_form(request, pk=None):
    category = get_object_or_404(Category, pk=pk) if pk else None
    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            saved_category = form.save()
            messages.success(request, "تم حفظ التصنيف بنجاح.")
            return redirect("staff_dashboard:category_edit", pk=saved_category.pk)
        messages.error(request, "يرجى مراجعة بيانات التصنيف.")
    else:
        form = CategoryForm(instance=category)

    return _render(
        request,
        "staff_dashboard/form.html",
        {
            "active_nav": "categories",
            "form": form,
            "page_title": "تعديل تصنيف" if category else "إضافة تصنيف",
            "page_subtitle": "تحكم في ظهور التصنيف وترتيبه وبيانات SEO الخاصة به.",
            "cancel_url": reverse("staff_dashboard:categories"),
            "delete_url": reverse("staff_dashboard:category_delete", args=[category.pk]) if category else "",
            "advanced_url": _admin_change_url(category) if category else "",
            "advanced_label": "تعديل متقدم في Django Admin",
            "multipart": True,
        },
    )


@superuser_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    products_count = category.product_set.count()
    if request.method == "POST":
        if products_count:
            messages.error(request, "لا يمكن حذف تصنيف يحتوي على منتجات. انقل المنتجات أو أخفِ التصنيف بدلًا من ذلك.")
        else:
            category.delete()
            messages.success(request, "تم حذف التصنيف بنجاح.")
        return redirect("staff_dashboard:categories")

    return _render(
        request,
        "staff_dashboard/confirm_delete.html",
        {
            "active_nav": "categories",
            "object_name": category.name,
            "object_type": "تصنيف",
            "cancel_url": reverse("staff_dashboard:categories"),
            "warning": f"هذا التصنيف يحتوي على {products_count} منتج. لن يُحذف إذا كان يحتوي على منتجات.",
        },
    )


@superuser_required
def orders_list(request):
    queryset = Order.objects.select_related("user").prefetch_related("items").order_by("-created_at")
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "all")

    if query:
        queryset = queryset.filter(
            Q(id__icontains=query)
            | Q(user__email__icontains=query)
            | Q(guest_email__icontains=query)
            | Q(shipping_name__icontains=query)
            | Q(shipping_phone__icontains=query)
            | Q(shipping_city__icontains=query)
        )
    if status != "all":
        queryset = queryset.filter(status=status)

    page_obj = _paginate(request, queryset, per_page=20)
    return _render(
        request,
        "staff_dashboard/orders_list.html",
        {
            "active_nav": "orders",
            "page_obj": page_obj,
            "orders": page_obj.object_list,
            "filters": {"q": query, "status": status},
            "statuses": _status_context(),
            "status_meta": ORDER_STATUS_META,
            "total_count": queryset.count(),
        },
    )


@superuser_required
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related("user").prefetch_related(
            "items",
            "items__product",
            "items__variant",
            "items__product_type",
        ),
        pk=pk,
    )
    if request.method == "POST":
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, "تم تحديث الطلب بنجاح.")
            return redirect("staff_dashboard:order_detail", pk=order.pk)
        messages.error(request, "يرجى مراجعة بيانات الطلب.")
    else:
        form = OrderStatusForm(instance=order)

    return _render(
        request,
        "staff_dashboard/order_detail.html",
        {
            "active_nav": "orders",
            "order": order,
            "items": order.items.all(),
            "form": form,
            "status_label": ORDER_STATUS_META.get(order.status, (order.status, "muted"))[0],
            "status_tone": ORDER_STATUS_META.get(order.status, (order.status, "muted"))[1],
            "advanced_url": _admin_change_url(order),
        },
    )


@superuser_required
def customers_list(request):
    User = get_user_model()
    queryset = User.objects.annotate(order_count=Count("orders")).order_by("-date_joined")
    query = request.GET.get("q", "").strip()
    role = request.GET.get("role", "all")
    status = request.GET.get("status", "all")

    if query:
        queryset = queryset.filter(
            Q(email__icontains=query)
            | Q(username__icontains=query)
            | Q(phone__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        )
    if role == "customers":
        queryset = queryset.filter(is_staff=False, is_superuser=False)
    elif role == "staff":
        queryset = queryset.filter(is_staff=True, is_superuser=False)
    elif role == "superusers":
        queryset = queryset.filter(is_superuser=True)
    if status == "active":
        queryset = queryset.filter(is_active=True)
    elif status == "inactive":
        queryset = queryset.filter(is_active=False)

    page_obj = _paginate(request, queryset, per_page=20)
    return _render(
        request,
        "staff_dashboard/customers_list.html",
        {
            "active_nav": "customers",
            "page_obj": page_obj,
            "customers": page_obj.object_list,
            "filters": {"q": query, "role": role, "status": status},
            "total_count": queryset.count(),
        },
    )


@superuser_required
def customer_form(request, pk):
    customer = get_object_or_404(get_user_model(), pk=pk)
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer, current_user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "تم حفظ بيانات المستخدم بنجاح.")
            return redirect("staff_dashboard:customer_edit", pk=customer.pk)
        messages.error(request, "يرجى مراجعة بيانات المستخدم.")
    else:
        form = CustomerForm(instance=customer, current_user=request.user)

    return _render(
        request,
        "staff_dashboard/form.html",
        {
            "active_nav": "customers",
            "form": form,
            "page_title": "تعديل مستخدم",
            "page_subtitle": "تعديل بيانات التواصل وحالة الحساب. تغيير كلمة المرور أو الصلاحيات المتقدمة يتم من Django Admin.",
            "cancel_url": reverse("staff_dashboard:customers"),
            "advanced_url": _admin_change_url(customer),
            "advanced_label": "إدارة متقدمة للمستخدم",
        },
    )


@superuser_required
def home_collections_list(request):
    queryset = HomeProductCollectionItem.objects.select_related("product", "product__category").order_by(
        "collection_type", "order", "-created_at"
    )
    query = request.GET.get("q", "").strip()
    collection_type = request.GET.get("type", "all")
    status = request.GET.get("status", "all")

    if query:
        queryset = queryset.filter(Q(product__name__icontains=query) | Q(product__category__name__icontains=query))
    if collection_type != "all":
        queryset = queryset.filter(collection_type=collection_type)
    if status == "active":
        queryset = queryset.filter(is_active=True)
    elif status == "inactive":
        queryset = queryset.filter(is_active=False)

    page_obj = _paginate(request, queryset, per_page=20)
    return _render(
        request,
        "staff_dashboard/home_collections_list.html",
        {
            "active_nav": "home_collections",
            "page_obj": page_obj,
            "items": page_obj.object_list,
            "filters": {"q": query, "type": collection_type, "status": status},
            "collection_choices": HomeProductCollectionItem.COLLECTION_CHOICES,
            "total_count": queryset.count(),
        },
    )


@superuser_required
def home_collection_form(request, pk=None):
    item = get_object_or_404(HomeProductCollectionItem, pk=pk) if pk else None
    if request.method == "POST":
        form = HomeCollectionItemForm(request.POST, instance=item)
        if form.is_valid():
            saved_item = form.save()
            messages.success(request, "تم حفظ عنصر الصفحة الرئيسية بنجاح.")
            return redirect("staff_dashboard:home_collection_edit", pk=saved_item.pk)
        messages.error(request, "يرجى مراجعة بيانات العنصر.")
    else:
        form = HomeCollectionItemForm(instance=item)

    return _render(
        request,
        "staff_dashboard/form.html",
        {
            "active_nav": "home_collections",
            "form": form,
            "page_title": "تعديل عنصر في الصفحة الرئيسية" if item else "إضافة عنصر للصفحة الرئيسية",
            "page_subtitle": "اختر المنتج والقسم الذي سيظهر فيه داخل تبويبات الصفحة الرئيسية.",
            "cancel_url": reverse("staff_dashboard:home_collections"),
            "delete_url": reverse("staff_dashboard:home_collection_delete", args=[item.pk]) if item else "",
            "advanced_url": _admin_change_url(item) if item else "",
            "advanced_label": "تعديل متقدم",
        },
    )


@superuser_required
def home_collection_delete(request, pk):
    item = get_object_or_404(HomeProductCollectionItem.objects.select_related("product"), pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "تم حذف العنصر من الصفحة الرئيسية.")
        return redirect("staff_dashboard:home_collections")

    return _render(
        request,
        "staff_dashboard/confirm_delete.html",
        {
            "active_nav": "home_collections",
            "object_name": str(item),
            "object_type": "عنصر الصفحة الرئيسية",
            "cancel_url": reverse("staff_dashboard:home_collections"),
            "warning": "سيتم حذف ظهور المنتج من هذا القسم فقط، ولن يتم حذف المنتج نفسه.",
        },
    )


@superuser_required
def settings_overview(request):
    context = {
        "active_nav": "settings",
        "site_settings": [
            ("النطاق الأساسي", getattr(settings, "CANONICAL_DOMAIN", "")),
            ("رابط الموقع", getattr(settings, "CANONICAL_BASE_URL", "")),
            ("وضع التطوير", "مفعل" if settings.DEBUG else "غير مفعل"),
            ("مسار الوسائط", getattr(settings, "MEDIA_URL", "")),
            ("مسار الملفات الثابتة", getattr(settings, "STATIC_URL", "")),
        ],
        "management_links": [
            {"label": "لوحة Django Admin الافتراضية", "url": reverse("admin:index"), "icon": "fa-screwdriver-wrench"},
            {"label": "الصفحة الرئيسية", "url": reverse("index"), "icon": "fa-house"},
            {"label": "خريطة الموقع", "url": reverse("sitemap"), "icon": "fa-sitemap"},
        ],
    }
    return _render(request, "staff_dashboard/settings.html", context)
