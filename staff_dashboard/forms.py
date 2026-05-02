from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from orders.models import Order
from products.models import (
    Category,
    Color,
    HeroSlide,
    HomeProductCollectionItem,
    Product,
    ProductColor,
    ProductType,
    ProductTypeColor,
    ProductTypeImage,
    Type,
)


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


def _clean_color_code(value):
    value = (value or "").strip()
    if not value:
        return ""
    if not value.startswith("#"):
        value = f"#{value}"
    if len(value) != 7:
        raise ValidationError("كود اللون يجب أن يكون مثل #ffcc00.")
    hex_part = value[1:]
    if any(char not in "0123456789abcdefABCDEF" for char in hex_part):
        raise ValidationError("كود اللون يجب أن يحتوي على أرقام أو حروف HEX فقط.")
    return value.lower()


class ColorChoiceMixin:
    color_field_name = "color"

    def _prepare_color_fields(self):
        self.fields[self.color_field_name].queryset = Color.objects.order_by("name")
        self.fields[self.color_field_name].required = False
        self.fields["new_color_name"].required = False
        self.fields["new_color_code"].required = False

    def _clean_color_choice(self):
        color = self.cleaned_data.get(self.color_field_name)
        new_color_name = (self.cleaned_data.get("new_color_name") or "").strip()
        new_color_code = self.cleaned_data.get("new_color_code") or ""

        if color and new_color_name:
            raise ValidationError("اختر لونًا موجودًا أو اكتب لونًا جديدًا، وليس الاثنين معًا.")
        if not color and not new_color_name:
            raise ValidationError("اختر لونًا موجودًا أو اكتب اسم لون جديد.")
        if color:
            return color, "", ""

        existing_color = Color.objects.filter(name__iexact=new_color_name).order_by("id").first()
        return existing_color, new_color_name, new_color_code

    def _save_color_choice(self):
        color = self.cleaned_data.get("_resolved_color")
        new_color_name = self.cleaned_data.get("_new_color_name") or ""
        new_color_code = self.cleaned_data.get("_new_color_code") or ""

        if not color:
            return Color.objects.create(name=new_color_name, code=new_color_code)

        if new_color_name and new_color_code and color.code != new_color_code:
            color.code = new_color_code
            color.save(update_fields=["code"])
        return color

    def clean_new_color_code(self):
        return _clean_color_code(self.cleaned_data.get("new_color_code"))


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


class ProductColorForm(ColorChoiceMixin, forms.ModelForm):
    new_color_name = forms.CharField(label="اسم لون جديد", required=False)
    new_color_code = forms.CharField(label="كود اللون", required=False)

    class Meta:
        model = ProductColor
        fields = ["color", "order"]
        labels = {
            "color": "لون موجود",
            "order": "ترتيب اللون",
        }

    def __init__(self, *args, product=None, **kwargs):
        self.product = product
        super().__init__(*args, **kwargs)
        self._prepare_color_fields()
        self.fields["new_color_code"].widget.attrs.update({"placeholder": "#f5c542", "dir": "ltr"})
        _apply_dashboard_widgets(self)

    def clean(self):
        cleaned_data = super().clean()
        if not self.product:
            raise ValidationError("يجب حفظ المنتج أولًا قبل إضافة الألوان.")

        color, new_color_name, new_color_code = self._clean_color_choice()
        if color and ProductColor.objects.filter(product=self.product, color=color).exclude(pk=self.instance.pk).exists():
            raise ValidationError("هذا اللون مربوط بهذا المنتج بالفعل.")
        cleaned_data["_resolved_color"] = color
        cleaned_data["_new_color_name"] = new_color_name
        cleaned_data["_new_color_code"] = new_color_code
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.product = self.product
        instance.color = self._save_color_choice()
        if commit:
            instance.save()
        return instance


class ProductTypeDashboardForm(forms.ModelForm):
    new_type_name = forms.CharField(label="اسم نوع جديد", required=False)

    class Meta:
        model = ProductType
        fields = ["type", "image", "price", "description", "order"]
        labels = {
            "type": "نوع موجود",
            "image": "صورة النوع",
            "price": "سعر هذا النوع",
            "description": "تفاصيل هذا النوع",
            "order": "ترتيب النوع",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, product=None, **kwargs):
        self.product = product
        super().__init__(*args, **kwargs)
        self.fields["type"].queryset = Type.objects.order_by("name")
        self.fields["type"].required = False
        self.fields["new_type_name"].required = False
        self.fields["description"].required = False
        _apply_dashboard_widgets(self)

    def clean(self):
        cleaned_data = super().clean()
        if not self.product:
            raise ValidationError("يجب حفظ المنتج أولًا قبل إضافة الأنواع.")

        selected_type = cleaned_data.get("type")
        new_type_name = (cleaned_data.get("new_type_name") or "").strip()
        if selected_type and new_type_name:
            raise ValidationError("اختر نوعًا موجودًا أو اكتب نوعًا جديدًا، وليس الاثنين معًا.")
        if not selected_type and not new_type_name:
            raise ValidationError("اختر نوعًا موجودًا أو اكتب اسم نوع جديد.")
        if new_type_name:
            selected_type = Type.objects.filter(name__iexact=new_type_name).order_by("id").first()

        if selected_type and ProductType.objects.filter(product=self.product, type=selected_type).exclude(pk=self.instance.pk).exists():
            raise ValidationError("هذا النوع مربوط بهذا المنتج بالفعل.")
        cleaned_data["_resolved_type"] = selected_type
        cleaned_data["_new_type_name"] = new_type_name
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.product = self.product
        instance.type = self.cleaned_data["_resolved_type"] or Type.objects.create(
            name=self.cleaned_data["_new_type_name"],
        )
        if commit:
            instance.save()
        return instance


class ProductTypeColorForm(ColorChoiceMixin, forms.ModelForm):
    new_color_name = forms.CharField(label="اسم لون جديد", required=False)
    new_color_code = forms.CharField(label="كود اللون", required=False)

    class Meta:
        model = ProductTypeColor
        fields = ["color", "order"]
        labels = {
            "color": "لون موجود",
            "order": "ترتيب اللون",
        }

    def __init__(self, *args, product_type=None, **kwargs):
        self.product_type = product_type
        super().__init__(*args, **kwargs)
        self._prepare_color_fields()
        self.fields["new_color_code"].widget.attrs.update({"placeholder": "#f5c542", "dir": "ltr"})
        _apply_dashboard_widgets(self)

    def clean(self):
        cleaned_data = super().clean()
        if not self.product_type:
            raise ValidationError("يجب حفظ النوع أولًا قبل إضافة الألوان.")

        color, new_color_name, new_color_code = self._clean_color_choice()
        duplicate = color and ProductTypeColor.objects.filter(
            product_type=self.product_type,
            color=color,
        ).exclude(pk=self.instance.pk).exists()
        if duplicate:
            raise ValidationError("هذا اللون مربوط بهذا النوع بالفعل.")
        cleaned_data["_resolved_color"] = color
        cleaned_data["_new_color_name"] = new_color_name
        cleaned_data["_new_color_code"] = new_color_code
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.product_type = self.product_type
        instance.color = self._save_color_choice()
        if commit:
            instance.save()
        return instance


class ProductTypeImageForm(forms.ModelForm):
    class Meta:
        model = ProductTypeImage
        fields = ["color", "image", "order"]
        labels = {
            "color": "لون الصورة",
            "image": "الصورة",
            "order": "ترتيب الصورة",
        }

    def __init__(self, *args, product_type=None, **kwargs):
        self.product_type = product_type
        super().__init__(*args, **kwargs)
        self.fields["color"].queryset = Color.objects.filter(
            product_type_colors__product_type=product_type,
        ).distinct().order_by("name") if product_type else Color.objects.none()
        self.fields["color"].required = False
        _apply_dashboard_widgets(self)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.product_type = self.product_type
        if commit:
            instance.save()
        return instance


class ColorForm(forms.ModelForm):
    class Meta:
        model = Color
        fields = ["name", "code"]
        labels = {
            "name": "اسم اللون",
            "code": "كود اللون",
        }
        widgets = {
            "code": forms.TextInput(attrs={"placeholder": "#f5c542", "dir": "ltr"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["code"].required = False
        _apply_dashboard_widgets(self)

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise ValidationError("اسم اللون مطلوب.")
        duplicate = Color.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists()
        if duplicate:
            raise ValidationError("يوجد لون بنفس الاسم بالفعل.")
        return name

    def clean_code(self):
        return _clean_color_code(self.cleaned_data.get("code"))


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


class HeroSlideForm(forms.ModelForm):
    class Meta:
        model = HeroSlide
        fields = ["title", "image", "link_url", "alt_text", "is_active", "order"]
        labels = {
            "title": "عنوان داخلي للشريحة",
            "image": "صورة السلايدر",
            "link_url": "رابط عند الضغط على الصورة",
            "alt_text": "النص البديل للصورة",
            "is_active": "نشطة",
            "order": "ترتيب العرض",
        }
        widgets = {
            "link_url": forms.TextInput(attrs={"dir": "ltr", "placeholder": "/products/ أو https://example.com"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].required = False
        self.fields["link_url"].required = False
        self.fields["alt_text"].required = False
        self.fields["image"].help_text = "يفضل صورة بنسبة 16:9 مثل 2048×1152 حتى تظهر بنفس جودة السلايدر الحالي."
        _apply_dashboard_widgets(self)

    def clean_link_url(self):
        return (self.cleaned_data.get("link_url") or "").strip()


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
