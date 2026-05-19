from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Address, AdminPasswordChangeRequest, UserOTP, UserProfile
from .utils import create_otp, verify_otp


User = get_user_model()


class AuthViewsTests(TestCase):
    def setUp(self):
        self.password = "CorrectPass123!"
        self.user = User.objects.create_user(
            username="existing",
            email="existing@example.com",
            password=self.password,
            phone="+201001112223",
            is_active=True,
        )

    def test_login_shows_wrong_password_message(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"identifier": self.user.email, "password": "WrongPass123!"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "كلمة المرور غير صحيحة")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_shows_missing_account_message_for_unknown_email(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"identifier": "missing@example.com", "password": self.password},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "لا يوجد حساب بهذه البيانات")

    def test_login_shows_missing_account_message_for_unknown_phone(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"identifier": "+201009990000", "password": self.password},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "لا يوجد حساب بهذه البيانات")

    def test_login_with_phone_succeeds(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"identifier": "+20 100 111 2223", "password": self.password},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_with_local_phone_format_succeeds(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"identifier": "01001112223", "password": self.password},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_with_local_phone_without_leading_zero_succeeds(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"identifier": "1001112223", "password": self.password},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_with_arabic_digits_phone_succeeds(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"identifier": "\u0660\u0661\u0660\u0660\u0661\u0661\u0661\u0662\u0662\u0662\u0663", "password": self.password},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_matches_legacy_un_normalized_phone_succeeds(self):
        legacy_user = User.objects.create_user(
            username="legacyphone",
            email="legacyphone@example.com",
            password=self.password,
            phone="0100 555 6666",
            is_active=True,
        )

        response = self.client.post(
            reverse("accounts:login"),
            {"identifier": "+201005556666", "password": self.password},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session["_auth_user_id"]), legacy_user.pk)

    def test_inactive_user_cannot_login(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        response = self.client.post(
            reverse("accounts:login"),
            {"identifier": self.user.email, "password": self.password},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "هذا الحساب غير مفعّل")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_register_shows_duplicate_phone_message(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "phone": "01001112223",
                "password1": "NewStrongPass123!",
                "password2": "NewStrongPass123!",
                "accept_terms": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "رقم الهاتف مستخدم من قبل")

    def test_register_shows_required_field_messages(self):
        response = self.client.post(reverse("accounts:register"), {})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "يرجى تصحيح الأخطاء الموضحة")
        self.assertContains(response, "اسم المستخدم مطلوب")
        self.assertContains(response, "البريد الإلكتروني مطلوب")
        self.assertContains(response, "رقم الهاتف مطلوب")

    @patch("accounts.views.create_otp")
    def test_register_success_creates_active_user_without_otp(self, create_otp):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "freshuser",
                "email": "fresh@example.com",
                "phone": "+20 100 999 8887",
                "password1": "NewStrongPass123!",
                "password2": "NewStrongPass123!",
                "accept_terms": "on",
            },
        )

        self.assertRedirects(response, reverse("accounts:login"))
        user = User.objects.get(email="fresh@example.com")
        self.assertTrue(user.is_active)
        self.assertEqual(user.phone, "+201009998887")
        self.assertNotIn("pending_verification_email", self.client.session)
        self.assertFalse(UserOTP.objects.filter(user=user).exists())
        create_otp.assert_not_called()

    @patch("accounts.views.create_otp")
    def test_register_allows_username_with_spaces(self, create_otp):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "Ahmed Ali",
                "email": "spaces@example.com",
                "phone": "01008887776",
                "password1": "NewStrongPass123!",
                "password2": "NewStrongPass123!",
                "accept_terms": "on",
            },
        )

        self.assertRedirects(response, reverse("accounts:login"))
        self.assertTrue(User.objects.filter(username="Ahmed Ali").exists())
        create_otp.assert_not_called()

    def test_verify_email_route_no_longer_requires_otp(self):
        response = self.client.get(reverse("accounts:verify_email"))

        self.assertRedirects(response, reverse("accounts:login"))
        self.assertNotIn("pending_verification_email", self.client.session)

    @patch("accounts.views.create_otp")
    def test_forgot_password_sends_code_and_opens_verify_page(self, create_otp):
        response = self.client.post(
            reverse("accounts:forgot_password"),
            {"email": " Existing@Example.COM "},
            follow=True,
        )

        self.assertRedirects(response, reverse("accounts:verify_reset_code"))
        self.assertEqual(self.client.session["password_reset_email"], self.user.email)
        self.assertNotIn("reset_code_verified", self.client.session)
        create_otp.assert_called_once_with(self.user.email, purpose="password_reset", user=self.user)
        self.assertContains(response, "تم إرسال كود التحقق إلى البريد الإلكتروني الخاص بالحساب")
        self.assertContains(response, self.user.email)

    @patch("accounts.views.create_otp")
    def test_forgot_password_handles_missing_account_without_opening_code_page(self, create_otp):
        response = self.client.post(
            reverse("accounts:forgot_password"),
            {"email": "missing@example.com"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "لا يوجد حساب مسجل بهذا البريد الإلكتروني")
        self.assertNotIn("password_reset_email", self.client.session)
        create_otp.assert_not_called()

    @patch("accounts.views.create_otp", side_effect=RuntimeError("mail down"))
    def test_forgot_password_handles_email_send_failure(self, create_otp):
        response = self.client.post(
            reverse("accounts:forgot_password"),
            {"email": self.user.email},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "تعذر إرسال كود التحقق الآن")
        self.assertNotIn("password_reset_email", self.client.session)
        create_otp.assert_called_once()


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="test@example.com",
    OTP_EXPIRY_MINUTES=10,
)
class OTPEmailTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="otpuser",
            email="otp@example.com",
            password="CorrectPass123!",
            is_active=True,
        )

    def test_create_otp_sends_email_and_stores_normalized_code(self):
        otp = create_otp(" OTP@Example.COM ", purpose="password_reset", user=self.user)

        self.assertEqual(otp.email, "otp@example.com")
        self.assertEqual(len(otp.code), 6)
        self.assertTrue(otp.code.isdigit())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(otp.code, mail.outbox[0].body)

        is_valid, result = verify_otp("OTP@example.com", otp.code, "password_reset")
        self.assertTrue(is_valid)
        self.assertEqual(result, otp)

    def test_create_otp_replaces_old_unused_code_for_same_purpose(self):
        first = create_otp(self.user.email, purpose="password_reset", user=self.user)
        second = create_otp(self.user.email, purpose="password_reset", user=self.user)

        self.assertFalse(UserOTP.objects.filter(pk=first.pk).exists())
        self.assertTrue(UserOTP.objects.filter(pk=second.pk, is_used=False).exists())

    def test_verify_otp_rejects_malformed_codes(self):
        is_valid, message = verify_otp(self.user.email, "123", "password_reset")

        self.assertFalse(is_valid)
        self.assertEqual(message, "الكود يجب أن يتكون من 6 أرقام")

    def test_create_otp_rejects_account_creation_purpose(self):
        with self.assertRaises(ValueError):
            create_otp(self.user.email, purpose="email_verification", user=self.user)


class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="profileuser",
            email="profile@example.com",
            password="StrongPass123!",
            phone="+201001234567",
            first_name="Ahmed",
            last_name="Ali",
            is_active=True,
        )

    def test_profile_requires_login(self):
        response = self.client.get(reverse("accounts:profile"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response["Location"])

    def test_profile_creates_missing_profile_and_displays_account_data(self):
        UserProfile.objects.filter(user=self.user).delete()
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:profile"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())
        self.assertContains(response, "Ahmed Ali")
        self.assertContains(response, self.user.email)
        self.assertContains(response, self.user.phone)
        self.assertContains(response, "العناوين المحفوظة")

    def test_profile_displays_full_address_data(self):
        Address.objects.create(
            user=self.user,
            full_name="Ahmed Ali",
            phone="+201001234567",
            country="مصر",
            city="القاهرة",
            street="شارع التحرير",
            postal_code="11511",
            is_default=True,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ahmed Ali")
        self.assertContains(response, "القاهرة")
        self.assertContains(response, "مصر")
        self.assertContains(response, "شارع التحرير")
        self.assertContains(response, "11511")
        self.assertContains(response, "افتراضي")

    def test_profile_updates_bio(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:profile"),
            {
                "email": self.user.email,
                "phone": self.user.phone,
                "bio": "نبذة محدثة",
            },
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        self.assertEqual(self.user.profile.bio, "نبذة محدثة")

    def test_profile_updates_email_and_phone(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:profile"),
            {
                "email": "updated@example.com",
                "phone": "01009998887",
                "bio": "نبذة محدثة",
            },
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "updated@example.com")
        self.assertEqual(self.user.phone, "+201009998887")
        self.assertEqual(self.user.profile.bio, "نبذة محدثة")

    def test_profile_changes_password_for_regular_user(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:profile"),
            {
                "form_action": "change_password",
                "old_password": "StrongPass123!",
                "new_password1": "NewStrongPass456!",
                "new_password2": "NewStrongPass456!",
            },
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPass456!"))
        self.assertTrue(self.client.login(email=self.user.email, password="NewStrongPass456!"))

    def test_profile_rejects_wrong_old_password(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:profile"),
            {
                "form_action": "change_password",
                "old_password": "WrongPass123!",
                "new_password1": "NewStrongPass456!",
                "new_password2": "NewStrongPass456!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("StrongPass123!"))

    def test_profile_admin_password_change_requires_other_admin_approval(self):
        admin = User.objects.create_superuser(
            username="adminprofile",
            email="adminprofile@example.com",
            password="AdminStrongPass123!",
            is_active=True,
        )
        User.objects.create_superuser(
            username="approver",
            email="approver-profile@example.com",
            password="ApproverStrongPass123!",
            is_active=True,
        )
        self.client.force_login(admin)

        response = self.client.post(
            reverse("accounts:profile"),
            {
                "form_action": "change_password",
                "old_password": "AdminStrongPass123!",
                "new_password1": "AdminNewStrongPass456!",
                "new_password2": "AdminNewStrongPass456!",
            },
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        change_request = AdminPasswordChangeRequest.objects.get(requester=admin)
        self.assertEqual(change_request.status, AdminPasswordChangeRequest.STATUS_PENDING)
        admin.refresh_from_db()
        self.assertTrue(admin.check_password("AdminStrongPass123!"))

    def test_profile_rejects_duplicate_email_and_phone(self):
        User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="StrongPass123!",
            phone="+201007776665",
            is_active=True,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:profile"),
            {
                "email": "other@example.com",
                "phone": "01007776665",
                "bio": "نبذة",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "البريد الإلكتروني مستخدم من قبل")
        self.assertContains(response, "رقم الهاتف مستخدم من قبل")
