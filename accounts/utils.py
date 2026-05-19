import secrets
from django.core.mail import send_mail
from django.conf import settings
from django.apps import apps
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import UserOTP


def normalize_email(email):
    return (email or "").strip().lower()


def generate_otp_code():
    """توليد كود OTP عشوائي من 6 أرقام"""
    return f"{secrets.randbelow(900000) + 100000:06d}"


def create_otp(email, purpose='email_verification', user=None):
    """
    إنشاء OTP جديد وإرساله عبر البريد الإلكتروني
    
    Args:
        email: البريد الإلكتروني
        purpose: الغرض من OTP (email_verification أو password_reset)
        user: المستخدم (اختياري)
    
    Returns:
        UserOTP object
    """
    email = normalize_email(email)
    if not email:
        raise ValueError("Email is required to create an OTP.")

    # حذف أي OTP قديم غير مستخدم لنفس البريد والغرض
    UserOTP.objects.filter(
        email=email, 
        purpose=purpose, 
        is_used=False
    ).delete()
    
    # توليد كود جديد
    code = generate_otp_code()
    
    # حساب وقت انتهاء الصلاحية
    expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
    expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
    
    # إنشاء OTP
    otp = UserOTP.objects.create(
        user=user,
        email=email,
        code=code,
        purpose=purpose,
        expires_at=expires_at
    )
    
    # إرسال البريد الإلكتروني، وحذف الكود إذا فشل الإرسال حتى لا يبقى كود لم يصل للمستخدم.
    try:
        send_otp_email(email, code, purpose)
    except Exception:
        otp.delete()
        raise
    
    return otp


def send_otp_email(email, code, purpose):
    """
    إرسال بريد إلكتروني يحتوي على كود OTP
    
    Args:
        email: البريد الإلكتروني المستلم
        code: كود OTP
        purpose: الغرض من OTP
    """
    if purpose == 'email_verification':
        subject = 'تأكيد حسابك في متجر الوسام'
        message = f"""
مرحباً بك في متجر الوسام!

لإكمال عملية التسجيل، يرجى إدخال الكود التالي:

{code}

هذا الكود صالح لمدة {getattr(settings, 'OTP_EXPIRY_MINUTES', 10)} دقائق فقط.

إذا لم تقم بإنشاء حساب، يرجى تجاهل هذه الرسالة.

مع تحيات،
فريق متجر الوسام
        """
    elif purpose == 'password_reset':
        subject = 'إعادة تعيين كلمة المرور - متجر الوسام'
        message = f"""
مرحباً،

تلقينا طلباً لإعادة تعيين كلمة المرور الخاصة بحسابك.

لإعادة تعيين كلمة المرور، يرجى إدخال الكود التالي:

{code}

هذا الكود صالح لمدة {getattr(settings, 'OTP_EXPIRY_MINUTES', 10)} دقائق فقط.

إذا لم تطلب إعادة تعيين كلمة المرور، يرجى تجاهل هذه الرسالة.

مع تحيات،
فريق متجر الوسام
        """
    else:
        subject = 'كود التحقق - متجر الوسام'
        message = f'كود التحقق الخاص بك هو: {code}'
    
    sent_count = send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
    if sent_count == 0:
        raise RuntimeError("OTP email was not sent.")


def verify_otp(email, code, purpose):
    """
    التحقق من صحة كود OTP
    
    Args:
        email: البريد الإلكتروني
        code: كود OTP المدخل
        purpose: الغرض من OTP
    
    Returns:
        tuple: (is_valid, otp_object or error_message)
    """
    email = normalize_email(email)
    code = (code or "").strip()
    if not email or not code:
        return False, 'الكود غير صحيح'
    if not code.isdigit() or len(code) != 6:
        return False, 'الكود يجب أن يتكون من 6 أرقام'

    try:
        otp = UserOTP.objects.filter(
            email=email,
            code=code,
            purpose=purpose,
            is_used=False
        ).latest('created_at')
        
        if not otp.is_valid():
            return False, 'انتهت صلاحية الكود، يرجى طلب كود جديد'
        
        return True, otp
        
    except UserOTP.DoesNotExist:
        return False, 'الكود غير صحيح'


def mark_otp_as_used(otp):
    """تعليم OTP كمستخدم"""
    otp.is_used = True
    otp.save()


class AdminPasswordChangeRequestUnavailable(RuntimeError):
    pass


def send_admin_password_change_approval_email(change_request, approval_url, recipients):
    requester = change_request.requester
    requester_name = requester.get_full_name() or requester.username or requester.email
    subject = "طلب موافقة على تغيير كلمة مرور أدمن"
    message = f"""
مرحباً،

الأدمن {requester_name} ({requester.email}) يريد تغيير كلمة المرور الخاصة به.

لا يتم تطبيق كلمة المرور الجديدة إلا بعد موافقة أدمن آخر من لوحة التحكم.

رابط صفحة الموافقة:
{approval_url}

إذا لم تكن تعرف سبب هذا الطلب، راجع حسابات الأدمن فوراً.
"""
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=list(recipients),
        fail_silently=False,
    )


def create_admin_password_change_request(user, password_hash, request=None):
    try:
        AdminPasswordChangeRequest = apps.get_model("accounts", "AdminPasswordChangeRequest")
    except LookupError as exc:
        raise AdminPasswordChangeRequestUnavailable(
            "Admin password approval model is not available. Deploy accounts.models and run migrations."
        ) from exc

    AdminPasswordChangeRequest.objects.filter(
        requester=user,
        status=AdminPasswordChangeRequest.STATUS_PENDING,
    ).update(status=AdminPasswordChangeRequest.STATUS_CANCELLED, decided_at=timezone.now())

    change_request = AdminPasswordChangeRequest.objects.create(
        requester=user,
        password_hash=password_hash,
    )
    approval_path = reverse(
        "staff_dashboard:admin_password_change_request_detail",
        args=[change_request.token],
    )
    approval_url = request.build_absolute_uri(approval_path) if request else approval_path

    recipients = list(
        user.__class__.objects.filter(is_active=True, is_superuser=True)
        .exclude(pk=user.pk)
        .exclude(email="")
        .values_list("email", flat=True)
    )
    if recipients:
        send_admin_password_change_approval_email(change_request, approval_url, recipients)
    return change_request, recipients
