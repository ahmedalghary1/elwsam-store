import random
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import UserOTP


def generate_otp_code():
    """توليد كود OTP عشوائي من 6 أرقام"""
    return str(random.randint(100000, 999999))


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
    
    # إرسال البريد الإلكتروني
    send_otp_email(email, code, purpose)
    
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
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


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
