import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import ListView
from django.contrib import messages
from django.db import transaction
from .models import User, UserProfile, Address, UserOTP
from .forms import UserRegisterForm, UserLoginForm, UserProfileForm, AddressForm
from .utils import create_otp, verify_otp, mark_otp_as_used

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
                    user.is_active = False  # تعطيل الحساب حتى يتم التحقق من البريد
                    user.save()

                    # إنشاء Profile تلقائياً
                    UserProfile.objects.get_or_create(user=user)

                    # إرسال OTP للتحقق من البريد
                    create_otp(user.email, purpose='email_verification', user=user)

                # حفظ البريد في الجلسة للتحقق
                request.session['pending_verification_email'] = user.email

                messages.success(request, "تم إنشاء الحساب بنجاح! تم إرسال كود التحقق إلى بريدك الإلكتروني.")
                return redirect('accounts:verify_email')
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

    def get_context(self, request, profile_form=None):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        addresses = request.user.addresses.all()
        default_address = addresses.filter(is_default=True).first()
        return {
            'profile': profile,
            'profile_form': profile_form or UserProfileForm(instance=profile, user=request.user),
            'addresses': addresses,
            'default_address': default_address,
            'addresses_count': addresses.count(),
        }

    def get(self, request):
        return render(request, self.template_name, self.get_context(request))

    def post(self, request):
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
        email = request.session.get('pending_verification_email')
        if not email:
            messages.error(request, "لا يوجد حساب في انتظار التحقق")
            return redirect('accounts:register')
        return render(request, self.template_name, {'email': email})

    def post(self, request):
        email = request.session.get('pending_verification_email')
        code = request.POST.get('code', '').strip()
        
        if not email:
            messages.error(request, "انتهت صلاحية الجلسة، يرجى التسجيل مرة أخرى")
            return redirect('accounts:register')
        
        # التحقق من الكود
        is_valid, result = verify_otp(email, code, 'email_verification')
        
        if is_valid:
            # تفعيل الحساب
            try:
                user = User.objects.get(email=email)
                user.is_active = True
                user.save()
                
                # تعليم OTP كمستخدم
                mark_otp_as_used(result)
                
                # حذف البريد من الجلسة
                del request.session['pending_verification_email']
                
                messages.success(request, "تم تفعيل حسابك بنجاح! يمكنك الآن تسجيل الدخول")
                return redirect('accounts:login')
            except User.DoesNotExist:
                messages.error(request, "حدث خطأ، يرجى المحاولة مرة أخرى")
        else:
            messages.error(request, result)
        
        return render(request, self.template_name, {'email': email})


# =========================
#  Resend OTP View
# =========================
class ResendOTPView(View):
    def post(self, request):
        email = request.session.get('pending_verification_email')
        if not email:
            messages.error(request, "لا يوجد حساب في انتظار التحقق")
            return redirect('accounts:register')
        
        try:
            user = User.objects.get(email=email)
            create_otp(email, purpose='email_verification', user=user)
            messages.success(request, "تم إرسال كود جديد إلى بريدك الإلكتروني")
        except User.DoesNotExist:
            messages.error(request, "حدث خطأ، يرجى المحاولة مرة أخرى")
        
        return redirect('accounts:verify_email')


# =========================
#  Forgot Password View
# =========================
class ForgotPasswordView(View):
    template_name = "accounts/forgot_password.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get('email', '').strip()
        
        try:
            user = User.objects.get(email=email)
            
            # إنشاء وإرسال OTP
            create_otp(email, purpose='password_reset', user=user)
            
            # حفظ البريد في الجلسة
            request.session['password_reset_email'] = email
            
            messages.success(request, "تم إرسال كود التحقق إلى بريدك الإلكتروني")
            return redirect('accounts:verify_reset_code')
            
        except User.DoesNotExist:
            messages.error(request, "لا يوجد حساب مسجل بهذا البريد الإلكتروني")
        
        return render(request, self.template_name)


# =========================
#  Verify Reset Code View
# =========================
class VerifyResetCodeView(View):
    template_name = "accounts/verify_reset_code.html"

    def get(self, request):
        email = request.session.get('password_reset_email')
        if not email:
            messages.error(request, "يرجى إدخال بريدك الإلكتروني أولاً")
            return redirect('accounts:forgot_password')
        return render(request, self.template_name, {'email': email})

    def post(self, request):
        email = request.session.get('password_reset_email')
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
        
        return render(request, self.template_name, {'email': email})


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
            user = User.objects.get(email=email)
            user.set_password(password1)
            user.save()
            
            # حذف بيانات الجلسة
            del request.session['password_reset_email']
            del request.session['reset_code_verified']
            
            messages.success(request, "تم تغيير كلمة المرور بنجاح! يمكنك الآن تسجيل الدخول")
            return redirect('accounts:login')
            
        except User.DoesNotExist:
            messages.error(request, "حدث خطأ، يرجى المحاولة مرة أخرى")
        
        return render(request, self.template_name)
