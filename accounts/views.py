from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.views import View
from django.views.generic import ListView
from django.contrib import messages
from .models import User, UserProfile, Address, Wishlist, UserOTP
from .forms import UserRegisterForm, UserLoginForm, UserProfileForm, AddressForm

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
            user = form.save()
            # يمكن إنشاء Profile تلقائيًا
            UserProfile.objects.create(user=user)
            messages.success(request, "تم إنشاء الحساب بنجاح، يمكنك تسجيل الدخول الآن.")
            return redirect('accounts:login')
        return render(request, self.template_name, {'form': form})


# =========================
#  Login View
# =========================
class LoginView(View):
    template_name = "accounts/login.html"

    def get(self, request):
        form = UserLoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"مرحبًا {user.username}")
                return redirect('core:home')
            else:
                messages.error(request, "بيانات الدخول غير صحيحة")
        return render(request, self.template_name, {'form': form})


# =========================
#  Logout View
# =========================
class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, "تم تسجيل الخروج بنجاح")
        return redirect('core:home')


# =========================
#  Profile View
# =========================
class ProfileView(View):
    template_name = "accounts/profile.html"

    def get(self, request):
        profile_form = UserProfileForm(instance=request.user.profile)
        addresses = request.user.addresses.all()
        return render(request, self.template_name, {
            'profile_form': profile_form,
            'addresses': addresses
        })

    def post(self, request):
        profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "تم تحديث الملف الشخصي بنجاح")
            return redirect('accounts:profile')
        addresses = request.user.addresses.all()
        return render(request, self.template_name, {
            'profile_form': profile_form,
            'addresses': addresses
        })


# =========================
#  Address CRUD Views
# =========================
class AddressCreateView(View):
    template_name = "accounts/address_form.html"

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


class AddressUpdateView(View):
    template_name = "accounts/address_form.html"

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


class AddressDeleteView(View):
    def post(self, request, pk):
        address = get_object_or_404(Address, pk=pk, user=request.user)
        address.delete()
        messages.success(request, "تم حذف العنوان بنجاح")
        return redirect('accounts:profile')


# =========================
#  Set Default Address
# =========================
def set_default_address(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
    address.is_default = True
    address.save()
    messages.success(request, "تم تعيين العنوان كافتراضي")
    return redirect('accounts:profile')


# =========================
#  Wishlist View
# =========================
class WishlistView(ListView):
    model = Wishlist
    template_name = "accounts/wishlist.html"
    context_object_name = "wishlist_items"

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related('product').order_by('-added_at')


# =========================
#  OTP Verification (اختياري)
# =========================
class OTPVerifyView(View):
    template_name = "accounts/otp_verify.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        code = request.POST.get('code')
        otp = UserOTP.objects.filter(user=request.user, code=code, is_used=False).first()
        if otp:
            otp.is_used = True
            otp.save()
            messages.success(request, "تم التحقق بنجاح")
            return redirect('core:home')
        else:
            messages.error(request, "رمز التحقق غير صحيح")
            return render(request, self.template_name)