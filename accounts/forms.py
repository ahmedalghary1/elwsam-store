import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.forms.models import InlineForeignKeyField, construct_instance
from .models import UserProfile, Address

User = get_user_model()


def normalize_phone(value):
    value = (value or "").strip()
    value = re.sub(r"[\s\-()]", "", value)
    if value.startswith("00"):
        value = f"+{value[2:]}"
    digits = phone_digits(value)
    if value.startswith("+"):
        return f"+{digits}"
    if digits.startswith("20") and len(digits) == 12:
        return f"+{digits}"
    if digits.startswith("0") and len(digits) == 11:
        return f"+20{digits[1:]}"
    return value


def phone_digits(value):
    return re.sub(r"\D", "", value or "")


def phone_lookup_keys(value):
    digits = phone_digits(normalize_phone(value))
    if not digits:
        return set()

    keys = {digits}
    if digits.startswith("20") and len(digits) == 12:
        keys.add(f"0{digits[2:]}")
    elif digits.startswith("0") and len(digits) == 11:
        keys.add(f"20{digits[1:]}")
    return keys


def phone_exists(value, exclude_user=None):
    target_keys = phone_lookup_keys(value)
    if not target_keys:
        return False

    users = User.objects.all()
    if exclude_user is not None and exclude_user.pk:
        users = users.exclude(pk=exclude_user.pk)

    if users.filter(phone=value).exists():
        return True

    return any(
        bool(phone_lookup_keys(user.phone) & target_keys)
        for user in users.exclude(phone__isnull=True).exclude(phone="").only("phone")
    )


# =========================
# User Registration Form
# =========================
class UserRegisterForm(UserCreationForm):
    error_messages = {
        "password_mismatch": "كلمتا المرور غير متطابقتان.",
    }
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'البريد الإلكتروني',
        'autocomplete': 'email',
    }))
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'اسم المستخدم',
        'autocomplete': 'username',
    }))
    phone = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': '+20 100 000 0000',
        'autocomplete': 'tel',
        'inputmode': 'tel',
    }))
    accept_terms = forms.BooleanField(
        required=True,
        error_messages={"required": "يجب الموافقة على شروط الاستخدام وسياسة الخصوصية."},
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password1', 'password2', 'accept_terms']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].error_messages.update({
            'required': 'اسم المستخدم مطلوب.',
            'max_length': 'اسم المستخدم طويل جداً.',
        })
        self.fields['email'].error_messages.update({
            'required': 'البريد الإلكتروني مطلوب.',
            'invalid': 'يرجى إدخال بريد إلكتروني صحيح.',
        })
        self.fields['phone'].error_messages.update({
            'required': 'رقم الهاتف مطلوب.',
            'max_length': 'رقم الهاتف طويل جداً.',
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'كلمة المرور',
            'autocomplete': 'new-password',
        })
        self.fields['password1'].error_messages.update({
            'required': 'كلمة المرور مطلوبة.',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'تأكيد كلمة المرور',
            'autocomplete': 'new-password',
        })
        self.fields['password2'].error_messages.update({
            'required': 'تأكيد كلمة المرور مطلوب.',
        })

    def clean_username(self):
        username = re.sub(r"\s+", " ", (self.cleaned_data.get('username') or '').strip())
        if not username:
            raise forms.ValidationError("اسم المستخدم مطلوب.")
        if username and User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("اسم المستخدم مستخدم من قبل.")
        return username

    def _post_clean(self):
        opts = self._meta
        exclude = self._get_validation_exclusions()

        for name, field in self.fields.items():
            if isinstance(field, InlineForeignKeyField):
                exclude.add(name)

        try:
            self.instance = construct_instance(self, self.instance, opts.fields, opts.exclude)
        except ValidationError as error:
            self._update_errors(error)

        try:
            self.instance.full_clean(
                exclude=exclude | {"username"},
                validate_unique=False,
                validate_constraints=False,
            )
        except ValidationError as error:
            self._update_errors(error)

        if self._validate_unique:
            self.validate_unique()
        if self._validate_constraints:
            self.validate_constraints()

        self.validate_password_for_user(self.instance)

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("البريد الإلكتروني مستخدم من قبل.")
        return email

    def clean_phone(self):
        raw_phone = self.cleaned_data.get('phone')
        phone = normalize_phone(raw_phone)
        digits = phone_digits(phone)

        if not phone:
            raise forms.ValidationError("رقم الهاتف مطلوب.")
        if not re.fullmatch(r"\+?\d+", phone):
            raise forms.ValidationError("يرجى إدخال رقم هاتف صحيح.")
        if len(digits) < 10 or len(digits) > 15:
            raise forms.ValidationError("رقم الهاتف يجب أن يكون بين 10 و15 رقماً.")
        if phone_exists(phone):
            raise forms.ValidationError("رقم الهاتف مستخدم من قبل.")

        return phone


# =========================
# User Login Form
# =========================
class UserLoginForm(forms.Form):
    identifier = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'البريد الإلكتروني أو رقم الجوال',
        'autocomplete': 'username',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'كلمة المرور',
        'autocomplete': 'current-password',
    }))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['identifier'].error_messages.update({
            'required': 'يرجى إدخال البريد الإلكتروني أو رقم الجوال.',
        })
        self.fields['password'].error_messages.update({
            'required': 'يرجى إدخال كلمة المرور.',
        })

    def clean_identifier(self):
        return (self.cleaned_data.get('identifier') or '').strip()

    def find_user(self, identifier):
        normalized_phone = normalize_phone(identifier)
        digits = phone_digits(normalized_phone)

        users = list(User.objects.filter(email__iexact=identifier)[:2])
        if not users and digits:
            users = list(User.objects.filter(phone=normalized_phone)[:2])
        if not users and digits:
            target_keys = phone_lookup_keys(identifier)
            users = [
                user for user in User.objects.exclude(phone__isnull=True).exclude(phone="").only("id", "phone", "email", "password", "is_active", "username")
                if phone_lookup_keys(user.phone) & target_keys
            ][:2]

        if len(users) > 1:
            raise forms.ValidationError("يوجد أكثر من حساب بهذا الرقم. يرجى تسجيل الدخول بالبريد الإلكتروني.")

        return users[0] if users else None

    def clean(self):
        cleaned_data = super().clean()
        identifier = cleaned_data.get('identifier')
        password = cleaned_data.get('password')

        if identifier and password:
            user = self.find_user(identifier)
            if user is None:
                raise forms.ValidationError("لا يوجد حساب بهذه البيانات.")

            if not user.check_password(password):
                raise forms.ValidationError("كلمة المرور غير صحيحة.")

            if not user.is_active:
                raise forms.ValidationError("هذا الحساب غير مفعّل. يرجى تأكيد البريد الإلكتروني أولاً.")

            cleaned_data['user'] = user
        return cleaned_data


# =========================
# User Profile Form
# =========================
class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'البريد الإلكتروني',
        'autocomplete': 'email',
    }))
    phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': '+20 100 000 0000',
        'autocomplete': 'tel',
        'inputmode': 'tel',
    }))

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user or getattr(self.instance, "user", None)
        if self.user is not None:
            self.fields['email'].initial = self.user.email
            self.fields['phone'].initial = self.user.phone
        self.fields['email'].error_messages.update({
            'required': 'البريد الإلكتروني مطلوب.',
            'invalid': 'يرجى إدخال بريد إلكتروني صحيح.',
        })
        self.fields['phone'].error_messages.update({
            'required': 'رقم الجوال مطلوب.',
            'max_length': 'رقم الهاتف طويل جداً.',
        })

    class Meta:
        model = UserProfile
        fields = ['email', 'phone', 'avatar', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'نبذة عنك...'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        queryset = User.objects.filter(email__iexact=email)
        if self.user is not None and self.user.pk:
            queryset = queryset.exclude(pk=self.user.pk)
        if queryset.exists():
            raise forms.ValidationError("البريد الإلكتروني مستخدم من قبل.")
        return email

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data.get('phone'))
        digits = phone_digits(phone)

        if not phone:
            raise forms.ValidationError("رقم الجوال مطلوب.")
        if not re.fullmatch(r"\+?\d+", phone):
            raise forms.ValidationError("يرجى إدخال رقم هاتف صحيح.")
        if len(digits) < 10 or len(digits) > 15:
            raise forms.ValidationError("رقم الهاتف يجب أن يكون بين 10 و15 رقماً.")
        if phone_exists(phone, exclude_user=self.user):
            raise forms.ValidationError("رقم الهاتف مستخدم من قبل.")

        return phone

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user is not None:
            self.user.email = self.cleaned_data['email']
            self.user.phone = self.cleaned_data['phone']
            if commit:
                self.user.save(update_fields=['email', 'phone'])
        if commit:
            profile.save()
        return profile


# =========================
# Address Form
# =========================
class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['full_name', 'phone', 'country', 'city', 'street', 'postal_code', 'is_default']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الاسم الكامل'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الهاتف'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الدولة'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'المدينة'
            }),
            'street': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'العنوان التفصيلي'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الرمز البريدي'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
