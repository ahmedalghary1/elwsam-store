import logging

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import ListView
from django.contrib import messages
from django.db import transaction
from .models import User, UserProfile, Address, UserOTP
from .forms import UserPasswordChangeForm, UserRegisterForm, UserLoginForm, UserProfileForm, AddressForm
from .utils import (
    AdminPasswordChangeRequestUnavailable,
    create_admin_password_change_request,
    create_otp,
    mark_otp_as_used,
    normalize_email,
    verify_otp,
)

logger = logging.getLogger(__name__)

# =========================
#  Register View
# =========================
class RegisterView(View):
    template_name = "accounts/register.html"

    def get(self, request):
        form = UserRegisterForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save(commit=False)
                    user.is_active = True
                    user.save()

                    # إنشاء Profile تلقائياً
                    UserProfile.objects.get_or_create(user=user)

                request.session.pop('pending_verification_email', None)
                messages.success(request, "تم إنشاء الحساب بنجاح. يمكنك الآن تسجيل الدخول مباشرة.")
                return redirect('accounts:login')
            except Exception:
                logger.exception("Failed to create account for email=%s", form.cleaned_data.get('email'))
                messages.error(request, "حدث خطأ أثناء إنشاء الحساب. يرجى المحاولة مرة أخرى.")
        else:
            messages.error(request, "يرجى تصحيح الأخطاء الموضحة ثم المحاولة مرة أخرى.")
        return render(request, self.template_name, {'form': form})


# =========================
#  Login View
# =========================
# class LoginView(View):
#     template_name = "accounts/login.html"

#     def get(self, request):
#         form = UserLoginForm()

#         return render(request, self.template_name, {'form': form})

#     def post(self, request):
#         form = UserLoginForm(request.POST)
#         if form.is_valid():
#             email = form.cleaned_data['email']
#             password = form.cleaned_data['password']
#             user = authenticate(request, email=email, password=password)
#             if user is not None:
#                 login(request, user)
#                 messages.success(request, f"مرحبًا {user.username}")

#                 # Get next URL or default to home
#                 next_url = request.POST.get('next') or request.GET.get('next') or 'index'

#                 # If user has cart in localStorage, redirect to cart for sync
#                 if request.POST.get('has_cart_data') == 'true':
#                     next_url = f"{next_url}{'&' if '?' in next_url else '?'}login=success"

#                 return redirect(next_url)
#             else:
#                 messages.error(request, "بيانات الدخول غير صحيحة")
#         return render(request, self.template_name, {'form': form})

class LoginView(View):
    template_name = "accounts/login.html"

    def get(self, request):
        form = UserLoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = UserLoginForm(request.POST)
        try:
            if form.is_valid():
                user = form.cleaned_data['user']
                login(request, user)
                messages.success(request, f"مرحبًا {user.username}")
                next_url = request.POST.get('next') or request.GET.get('next') or 'index'
                if request.POST.get('has_cart_data') == 'true':
                    next_url = f"{next_url}{'&' if '?' in next_url else '?'}login=success"
                return redirect(next_url)
        except Exception:
            logger.exception("Failed login attempt for identifier=%s", request.POST.get('identifier', ''))
            messages.error(request, "حدث خطأ أثناء تسجيل الدخول. يرجى المحاولة مرة أخرى.")
            return render(request, self.template_name, {'form': form})

        if not form.non_field_errors():
            messages.error(request, "يرجى إدخال بيانات تسجيل الدخول بشكل صحيح.")
        return render(request, self.template_name, {'form': form})
# =========================
#  Logout View
# =========================
class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, "تم تسجيل الخروج بنجاح")
        return redirect('index')


# =========================
#  Profile View
# =========================
class ProfileView(LoginRequiredMixin, View):
    template_name = "accounts/profile.html"
    login_url = "accounts:login"

    def get_context(self, request, profile_form=None, password_form=None):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        addresses = request.user.addresses.all()
        default_address = addresses.filter(is_default=True).first()
        return {
            'profile': profile,
            'profile_form': profile_form or UserProfileForm(instance=profile, user=request.user),
            'password_form': password_form or UserPasswordChangeForm(user=request.user),
            'addresses': addresses,
            'default_address': default_address,
            'addresses_count': addresses.count(),
        }

    def get(self, request):
        return render(request, self.template_name, self.get_context(request))

    def post(self, request):
        if request.POST.get('form_action') == 'change_password':
            password_form = UserPasswordChangeForm(request.POST, user=request.user)
            if password_form.is_valid():
                new_password = password_form.cleaned_data['new_password1']
                if request.user.is_superuser:
                    other_admins_exist = User.objects.filter(
                        is_active=True,
                        is_superuser=True,
                    ).exclude(pk=request.user.pk).exclude(email="").exists()
                    if not other_admins_exist:
                        messages.error(request, "لا يمكن تغيير كلمة مرور الأدمن بدون وجود أدمن آخر نشط للموافقة.")
                        return render(request, self.template_name, self.get_context(request, password_form=password_form))

                    try:
                        _change_request, recipients = create_admin_password_change_request(
                            user=request.user,
                            password_hash=make_password(new_password),
                            request=request,
                        )
                    except AdminPasswordChangeRequestUnavailable:
                        messages.error(
                            request,
                            "ميزة موافقة تغيير كلمة مرور الأدمن غير مكتملة على السيرفر. يرجى رفع ملفات accounts وتشغيل migrations ثم المحاولة مرة أخرى.",
                        )
                        return render(request, self.template_name, self.get_context(request, password_form=password_form))

                    messages.success(
                        request,
                        f"تم إرسال طلب تغيير كلمة المرور إلى {len(recipients)} أدمن للموافقة. لن تتغير كلمة المرور قبل الموافقة.",
                    )
                    return redirect('accounts:profile')

                request.user.set_password(new_password)
                request.user.save(update_fields=['password'])
                update_session_auth_hash(request, request.user)
                messages.success(request, "تم تغيير كلمة المرور بنجاح.")
                return redirect('accounts:profile')

            messages.error(request, "يرجى مراجعة بيانات تغيير كلمة المرور.")
            return render(request, self.template_name, self.get_context(request, password_form=password_form))

        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "تم تحديث الملف الشخصي بنجاح")
            return redirect('accounts:profile')
        messages.error(request, "يرجى تصحيح بيانات الملف الشخصي ثم المحاولة مرة أخرى.")
        return render(request, self.template_name, self.get_context(request, profile_form))


# =========================
#  Address CRUD Views
# =========================
class AddressCreateView(LoginRequiredMixin, View):
    template_name = "accounts/address_form.html"
    login_url = "accounts:login"

    def get(self, request):
        form = AddressForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            # إذا تم اختيار كعنوان افتراضي، قم بإلغاء الافتراضي السابق
            if address.is_default:
                Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
            address.save()
            messages.success(request, "تم إضافة العنوان بنجاح")
            return redirect('accounts:profile')
        return render(request, self.template_name, {'form': form})


class AddressUpdateView(LoginRequiredMixin, View):
    template_name = "accounts/address_form.html"
    login_url = "accounts:login"

    def get(self, request, pk):
        address = get_object_or_404(Address, pk=pk, user=request.user)
        form = AddressForm(instance=address)
        return render(request, self.template_name, {'form': form})

    def post(self, request, pk):
        address = get_object_or_404(Address, pk=pk, user=request.user)
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            if form.cleaned_data['is_default']:
                Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
            form.save()
            messages.success(request, "تم تحديث العنوان بنجاح")
            return redirect('accounts:profile')
        return render(request, self.template_name, {'form': form})


class AddressDeleteView(LoginRequiredMixin, View):
    login_url = "accounts:login"

    def post(self, request, pk):
        address = get_object_or_404(Address, pk=pk, user=request.user)
        address.delete()
        messages.success(request, "تم حذف العنوان بنجاح")
        return redirect('accounts:profile')


# =========================
#  Set Default Address
# =========================
@login_required(login_url="accounts:login")
def set_default_address(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
    address.is_default = True
    address.save()
    messages.success(request, "تم تعيين العنوان كافتراضي")
    return redirect('accounts:profile')


# =========================
#  Email Verification View
# =========================
class VerifyEmailView(View):
    template_name = "accounts/verify_email.html"

    def get(self, request):
        request.session.pop('pending_verification_email', None)
        messages.info(request, "تفعيل البريد غير مطلوب حالياً. يمكنك تسجيل الدخول مباشرة.")
        return redirect('accounts:login')

    def post(self, request):
        return self.get(request)


# =========================
#  Resend OTP View
# =========================
class ResendOTPView(View):
    def post(self, request):
        request.session.pop('pending_verification_email', None)
        messages.info(request, "أكواد التحقق تستخدم الآن لإعادة تعيين كلمة المرور فقط.")
        return redirect('accounts:login')


# =========================
#  Forgot Password View
# =========================
class ForgotPasswordView(View):
    template_name = "accounts/forgot_password.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        email = normalize_email(request.POST.get('email', ''))
        if not email:
            messages.error(request, "يرجى إدخال البريد الإلكتروني المرتبط بحسابك.")
            return render(request, self.template_name)

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            messages.error(request, "لا يوجد حساب مسجل بهذا البريد الإلكتروني.")
            return render(request, self.template_name, {"email": email})

        try:
            create_otp(user.email, purpose='password_reset', user=user)
        except Exception:
            logger.exception("Failed to send password reset OTP for user_id=%s", user.pk)
            messages.error(
                request,
                "تعذر إرسال كود التحقق الآن. يرجى المحاولة مرة أخرى بعد قليل.",
            )
            return render(request, self.template_name, {"email": email})

        request.session['password_reset_email'] = normalize_email(user.email)
        request.session.pop('reset_code_verified', None)

        messages.success(
            request,
            "تم إرسال كود التحقق إلى البريد الإلكتروني الخاص بالحساب، وتم فتح صفحة إدخال الكود تلقائيًا.",
        )
        return redirect('accounts:verify_reset_code')


# =========================
#  Verify Reset Code View
# =========================
class VerifyResetCodeView(View):
    template_name = "accounts/verify_reset_code.html"

    def get(self, request):
        email = normalize_email(request.session.get('password_reset_email'))
        if not email:
            messages.error(request, "يرجى إدخال بريدك الإلكتروني أولاً")
            return redirect('accounts:forgot_password')
        return render(
            request,
            self.template_name,
            {
                'email': email,
                'otp_expiry_minutes': getattr(settings, 'OTP_EXPIRY_MINUTES', 10),
            },
        )

    def post(self, request):
        email = normalize_email(request.session.get('password_reset_email'))
        code = request.POST.get('code', '').strip()
        
        if not email:
            messages.error(request, "انتهت صلاحية الجلسة")
            return redirect('accounts:forgot_password')
        
        # التحقق من الكود
        is_valid, result = verify_otp(email, code, 'password_reset')
        
        if is_valid:
            # تعليم OTP كمستخدم
            mark_otp_as_used(result)
            
            # حفظ حالة التحقق في الجلسة
            request.session['reset_code_verified'] = True
            
            messages.success(request, "تم التحقق من الكود بنجاح")
            return redirect('accounts:reset_password')
        else:
            messages.error(request, result)
        
        return render(
            request,
            self.template_name,
            {
                'email': email,
                'otp_expiry_minutes': getattr(settings, 'OTP_EXPIRY_MINUTES', 10),
            },
        )


# =========================
#  Reset Password View
# =========================
class ResetPasswordView(View):
    template_name = "accounts/reset_password.html"

    def get(self, request):
        if not request.session.get('reset_code_verified'):
            messages.error(request, "يرجى التحقق من الكود أولاً")
            return redirect('accounts:forgot_password')
        return render(request, self.template_name)

    def post(self, request):
        if not request.session.get('reset_code_verified'):
            messages.error(request, "يرجى التحقق من الكود أولاً")
            return redirect('accounts:forgot_password')
        
        email = request.session.get('password_reset_email')
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        
        if password1 != password2:
            messages.error(request, "كلمتا المرور غير متطابقتين")
            return render(request, self.template_name)
        
        if len(password1) < 8:
            messages.error(request, "كلمة المرور يجب أن تكون 8 أحرف على الأقل")
            return render(request, self.template_name)
        
        try:
            user = User.objects.get(email__iexact=email)
            if user.is_superuser:
                other_admins_exist = User.objects.filter(
                    is_active=True,
                    is_superuser=True,
                ).exclude(pk=user.pk).exclude(email="").exists()
                if not other_admins_exist:
                    messages.error(request, "لا يمكن تغيير كلمة مرور الأدمن بدون وجود أدمن آخر نشط للموافقة.")
                    return render(request, self.template_name)

                try:
                    _change_request, recipients = create_admin_password_change_request(
                        user=user,
                        password_hash=make_password(password1),
                        request=request,
                    )
                except AdminPasswordChangeRequestUnavailable:
                    messages.error(
                        request,
                        "ميزة موافقة تغيير كلمة مرور الأدمن غير مكتملة على السيرفر. يرجى رفع ملفات accounts وتشغيل migrations ثم المحاولة مرة أخرى.",
                    )
                    return render(request, self.template_name)

                request.session.pop('password_reset_email', None)
                request.session.pop('reset_code_verified', None)
                messages.success(
                    request,
                    f"تم إرسال طلب تغيير كلمة المرور إلى {len(recipients)} أدمن للموافقة. لن تتغير كلمة المرور قبل الموافقة.",
                )
                return redirect('accounts:login')

            user.set_password(password1)
            user.save()
            
            # حذف بيانات الجلسة
            request.session.pop('password_reset_email', None)
            request.session.pop('reset_code_verified', None)
            
            messages.success(request, "تم تغيير كلمة المرور بنجاح! يمكنك الآن تسجيل الدخول")
            return redirect('accounts:login')
            
        except User.DoesNotExist:
            messages.error(request, "حدث خطأ، يرجى المحاولة مرة أخرى")
        
        return render(request, self.template_name)
