from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    # Email Verification
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('resend-otp/', views.ResendOTPView.as_view(), name='resend_otp'),

    # Password Reset
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('verify-reset-code/', views.VerifyResetCodeView.as_view(), name='verify_reset_code'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset_password'),

    # Profile
    path('profile/', views.ProfileView.as_view(), name='profile'),

    # Addresses
    path('addresses/add/', views.AddressCreateView.as_view(), name='address_create'),
    path('addresses/<int:pk>/edit/', views.AddressUpdateView.as_view(), name='address_update'),
    path('addresses/<int:pk>/delete/', views.AddressDeleteView.as_view(), name='address_delete'),
    path('addresses/<int:pk>/set-default/', views.set_default_address, name='set_default_address'),
]