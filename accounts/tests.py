from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Address, UserProfile


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
    def test_register_success_creates_inactive_user_and_redirects_to_verification(self, create_otp):
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

        self.assertRedirects(response, reverse("accounts:verify_email"))
        user = User.objects.get(email="fresh@example.com")
        self.assertFalse(user.is_active)
        self.assertEqual(user.phone, "+201009998887")
        self.assertEqual(self.client.session["pending_verification_email"], user.email)
        create_otp.assert_called_once_with(user.email, purpose="email_verification", user=user)

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

        self.assertRedirects(response, reverse("accounts:verify_email"))
        self.assertTrue(User.objects.filter(username="Ahmed Ali").exists())


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
