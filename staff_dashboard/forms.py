from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from orders.models import Order
from products.models import Category, HomeProductCollectionItem, Product


def _apply_dashboard_widgets(form):
    for field in form.fields.values():
        widget = field.widget
        widget_type = getattr(widget, "input_type", "")

        if widget_type == "checkbox":
            widget.attrs.setdefault("class", "dash-checkbox")
            continue

        if isinstance(widget, forms.Select):
            widget.attrs.setdefault("class", "dash-input dash-select")
        elif isinstance(widget, forms.Textarea):
            widget.attrs.setdefault("class", "dash-input dash-textarea")
            widget.attrs.setdefault("rows", 4)
        elif isinstance(widget, forms.ClearableFileInput):
            widget.attrs.setdefault("class", "dash-input dash-file")
        else:
            widget.attrs.setdefault("class", "dash-input")


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "slug",
            "category",
            "description",
            "image",
            "price",
            "old_price",
            "stock",
            "is_active",
            "is_new",
            "is_hot",
            "has_colors",
            "has_patterns",
            "has_product_level_sizes",
            "rating",
            "order",
            "seo_title",
            "meta_description",
            "seo_h1",
            "seo_description",
            "focus_keywords",
        ]
        labels = {
            "name": "اسم المنتج",
            "slug": "الرابط المختصر",
            "category": "التصنيف",
            "description": "وصف المنتج",
            "image": "الصورة الرئيسية",
            "price": "السعر الحالي",
            "old_price": "السعر قبل الخصم",
            "stock": "مخزون المنتج البسيط",
            "is_active": "ظاهر في الموقع",
            "is_new": "منتج جديد",
            "is_hot": "الأكثر طلبًا",
            "has_colors": "له ألوان",
            "has_patterns": "له أنماط",
            "has_product_level_sizes": "له مقاسات",
            "rating": "التقييم",
            "order": "ترتيب العرض",
            "seo_title": "عنوان SEO",
            "meta_description": "وصف محركات البحث",
            "seo_h1": "عنوان H1",
            "seo_description": "وصف SEO طويل",
            "focus_keywords": "الكلمات المفتاحية",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "seo_description": forms.Textarea(attrs={"rows": 4}),
            "focus_keywords": forms.Textarea(attrs={"rows": 3}),
            "meta_description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.order_by("order", "name")
        self.fields["slug"].required = False
        self.fields["old_price"].required = False
        self.fields["seo_title"].required = False
        self.fields["meta_description"].required = False
        self.fields["seo_h1"].required = False
        self.fields["seo_description"].required = False
        self.fields["focus_keywords"].required = False
        _apply_dashboard_widgets(self)

    def clean_rating(self):
        rating = self.cleaned_data.get("rating")
        if rating is not None and not 0 <= rating <= 5:
            raise ValidationError("التقييم يجب أن يكون بين 0 و 5.")
        return rating

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get("price")
        old_price = cleaned_data.get("old_price")
        stock = cleaned_data.get("stock")

        if price is not None and price < 0:
            self.add_error("price", "السعر لا يمكن أن يكون أقل من صفر.")
        if old_price is not None and old_price < 0:
            self.add_error("old_price", "السعر قبل الخصم لا يمكن أن يكون أقل من صفر.")
        if stock is not None and stock < 0:
            self.add_error("stock", "المخزون لا يمكن أن يكون أقل من صفر.")
        return cleaned_data


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = [
            "name",
            "slug",
            "description",
            "image",
            "icon",
            "is_active",
            "is_hot",
            "order",
            "seo_title",
            "meta_description",
            "seo_intro",
        ]
        labels = {
            "name": "اسم التصنيف",
            "slug": "الرابط المختصر",
            "description": "الوصف",
            "image": "الصورة",
            "icon": "أيقونة مختصرة",
            "is_active": "ظاهر في الموقع",
            "is_hot": "تصنيف مميز",
            "order": "ترتيب العرض",
            "seo_title": "عنوان SEO",
            "meta_description": "وصف محركات البحث",
            "seo_intro": "مقدمة صفحة التصنيف",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "meta_description": forms.Textarea(attrs={"rows": 3}),
            "seo_intro": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        self.fields["description"].required = False
        self.fields["seo_title"].required = False
        self.fields["meta_description"].required = False
        self.fields["seo_intro"].required = False
        _apply_dashboard_widgets(self)


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "status",
            "payment_method",
            "contact_method",
            "shipping_name",
            "shipping_phone",
            "shipping_city",
            "shipping_address",
            "shipping_notes",
            "order_notes",
        ]
        labels = {
            "status": "حالة الطلب",
            "payment_method": "طريقة الدفع",
            "contact_method": "طريقة التواصل",
            "shipping_name": "اسم المستلم",
            "shipping_phone": "رقم الهاتف",
            "shipping_city": "المدينة",
            "shipping_address": "عنوان الشحن",
            "shipping_notes": "ملاحظات الشحن",
            "order_notes": "ملاحظات الطلب",
        }
        widgets = {
            "shipping_address": forms.Textarea(attrs={"rows": 4}),
            "shipping_notes": forms.Textarea(attrs={"rows": 3}),
            "order_notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_dashboard_widgets(self)


class HomeCollectionItemForm(forms.ModelForm):
    class Meta:
        model = HomeProductCollectionItem
        fields = ["collection_type", "product", "is_active", "order"]
        labels = {
            "collection_type": "قسم الصفحة الرئيسية",
            "product": "المنتج",
            "is_active": "نشط",
            "order": "ترتيب العرض",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.select_related("category").order_by("name")
        _apply_dashboard_widgets(self)

    def clean(self):
        cleaned_data = super().clean()
        collection_type = cleaned_data.get("collection_type")
        product = cleaned_data.get("product")
        if collection_type and product:
            exists = HomeProductCollectionItem.objects.filter(
                collection_type=collection_type,
                product=product,
            ).exclude(pk=self.instance.pk).exists()
            if exists:
                raise ValidationError("هذا المنتج موجود بالفعل داخل نفس قسم الصفحة الرئيسية.")
        return cleaned_data


class CustomerForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ["username", "first_name", "last_name", "email", "phone", "is_active", "is_staff"]
        labels = {
            "username": "اسم المستخدم",
            "first_name": "الاسم الأول",
            "last_name": "اسم العائلة",
            "email": "البريد الإلكتروني",
            "phone": "رقم الهاتف",
            "is_active": "الحساب مفعل",
            "is_staff": "له دخول للوحة Django Admin",
        }

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop("current_user", None)
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.current_user and self.instance.pk == self.current_user.pk:
            self.fields["is_active"].disabled = True
        _apply_dashboard_widgets(self)

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.current_user and user.pk == self.current_user.pk:
            user.is_active = True
        if commit:
            user.save()
            self.save_m2m()
        return user
