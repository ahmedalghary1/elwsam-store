import secrets
from django.conf import settings
from django.apps import apps
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .email_utils import send_branded_email
from .models import UserOTP


def normalize_email(email):
    return (email or "").strip().lower()


def generate_otp_code():
    """توليد كود OTP عشوائي من 6 أرقام"""
    return f"{secrets.randbelow(900000) + 100000:06d}"


def create_otp(email, purpose='password_reset', user=None):
    """
    إنشاء OTP جديد وإرساله عبر البريد الإلكتروني
    
    Args:
        email: البريد الإلكتروني
        purpose: الغرض من OTP. حالياً يستخدم فقط لإعادة تعيين كلمة المرور.
        user: المستخدم (اختياري)
    
    Returns:
        UserOTP object
    """
    email = normalize_email(email)
    if not email:
        raise ValueError("Email is required to create an OTP.")
    if purpose != 'password_reset':
        raise ValueError("OTP is only supported for password reset.")

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
    if purpose == 'password_reset':
        expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
        subject = 'كود إعادة تعيين كلمة المرور - متجر الوسام'
        message = f"""مرحباً،

تلقينا طلباً لإعادة تعيين كلمة المرور الخاصة بحسابك في متجر الوسام.

كود التحقق الخاص بك هو: {code}

هذا الكود صالح لمدة {expiry_minutes} دقائق فقط.

إذا لم تطلب إعادة تعيين كلمة المرور، يرجى تجاهل هذه الرسالة ولن يتم تغيير كلمة المرور.

مع تحيات،
فريق متجر الوسام
"""
        body_lines = [
            "تلقينا طلباً لإعادة تعيين كلمة المرور الخاصة بحسابك في متجر الوسام.",
            f"استخدم كود التحقق التالي خلال {expiry_minutes} دقائق فقط لإكمال تغيير كلمة المرور.",
            "إذا لم تطلب إعادة تعيين كلمة المرور، تجاهل هذه الرسالة ولن يتم تغيير كلمة المرور.",
        ]
    else:
        raise ValueError("Unsupported OTP purpose.")
    
    sent_count = send_branded_email(
        subject=subject,
        text_message=message,
        recipient_list=[email],
        title="إعادة تعيين كلمة المرور",
        intro="استخدم الكود التالي لإكمال التحقق.",
        body_lines=body_lines,
        code=code,
        footer_note="لا تشارك هذا الكود مع أي شخص. فريق متجر الوسام لن يطلب منك الكود خارج صفحة إعادة التعيين.",
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
    message = f"""مرحباً،

الأدمن {requester_name} ({requester.email}) يريد تغيير كلمة المرور الخاصة به.

لا يتم تطبيق كلمة المرور الجديدة إلا بعد موافقة أدمن آخر من لوحة التحكم.

رابط صفحة الموافقة:
{approval_url}

إذا لم تكن تعرف سبب هذا الطلب، راجع حسابات الأدمن فوراً.
"""
    send_branded_email(
        subject=subject,
        recipient_list=list(recipients),
        text_message=message,
        title="طلب موافقة على تغيير كلمة مرور أدمن",
        intro="يوجد طلب جديد يحتاج مراجعة أدمن آخر قبل تطبيقه.",
        body_lines=[
            f"الأدمن {requester_name} ({requester.email}) طلب تغيير كلمة المرور الخاصة به.",
            "لن يتم تطبيق كلمة المرور الجديدة إلا بعد موافقة أدمن آخر من لوحة التحكم.",
            "إذا لم تكن تعرف سبب هذا الطلب، راجع حسابات الأدمن فوراً.",
        ],
        action_label="مراجعة الطلب",
        action_url=approval_url,
        footer_note="هذا الإجراء يحمي حسابات الأدمن من تغيير كلمات المرور بدون موافقة مستقلة.",
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
