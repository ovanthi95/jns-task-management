"""Tests for API 01 - POST /api/auth/login

Test owner: Manatka
Implementation owner: Ovanthi

Cases from playbook 9.4: successful login, wrong password,
inactive/unknown user, session cookie/session creation. Plus the rules
sp_get_login_user enforces: active JNS organisation only, case-insensitive
email, and no password hash in the response.

Tests only. The implementation is not modified here; defects are reported
to the owner (playbook section 6).

MySQL only; sp_get_login_user is loaded before the class-level transaction.
"""

from django.test import TestCase
from rest_framework import status

from data_access.sp_loader import load_stored_procedures
from users.models import Organisation, Role, User

URL = "/api/auth/login"
PASSWORD = "Correct#Horse9"


class LoginApiTests(TestCase):
    @classmethod
    def setUpClass(cls):
        load_stored_procedures("users/sp_get_login_user")
        super().setUpClass()

    @classmethod
    def setUpTestData(cls):
        cls.admin_role = Role.objects.create(role_name="Admin")
        cls.employee_role = Role.objects.create(role_name="Employee")

        cls.jns = cls._organisation("JNS Business Solutions", "Active")
        cls.other_org = cls._organisation("Unrelated Charity", "Active")
        cls.inactive_org = cls._organisation("JNS Business Solutions Old", "Inactive")

        cls.user = cls._user(cls.jns, "staff@jns.test", cls.employee_role)
        cls.inactive_user = cls._user(cls.jns, "gone@jns.test", cls.employee_role, status="Inactive")
        cls.outsider = cls._user(cls.other_org, "someone@charity.test", cls.admin_role)

    @staticmethod
    def _organisation(name, org_status):
        return Organisation.objects.create(
            organisation_name=name, organisation_type="Accounting",
            email=f"info@{name.split()[0].lower()}.test", phone="09-000-0000",
            address="Auckland", status=org_status,
        )

    @staticmethod
    def _user(org, email, role, status="Active"):
        return User.objects.create_user(
            email=email, organisation=org, role=role, password=PASSWORD,
            first_name="Test", last_name="User", status=status,
        )

    def _login(self, email, password):
        return self.client.post(
            URL, data={"email": email, "password": password},
            content_type="application/json",
        )

    # -- success -----------------------------------------------------------

    def test_valid_login_returns_200_with_safe_user(self):
        response = self._login("staff@jns.test", PASSWORD)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()

        self.assertEqual(body["message"], "Login successful.")

        user = body["user"]

        self.assertEqual(user["user_id"], self.user.user_id)
        self.assertEqual(user["email"], "staff@jns.test")
        self.assertEqual(user["role_name"], "Employee")
        self.assertEqual(user["organisation_name"], "JNS Business Solutions")
        self.assertNotIn("password_hash", user)
        self.assertNotIn("password", user)

    def test_valid_login_creates_session_and_cookie(self):
        response = self._login("staff@jns.test", PASSWORD)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("sessionid", response.cookies)
        self.assertEqual(self.client.session.get("user_id"), self.user.user_id)

    def test_login_cycles_session_key(self):
        self._login("staff@jns.test", PASSWORD)
        first_key = self.client.session.session_key

        self._login("staff@jns.test", PASSWORD)
        second_key = self.client.session.session_key

        self.assertNotEqual(first_key, second_key)
        self.assertEqual(self.client.session.get("user_id"), self.user.user_id)

    def test_email_is_case_insensitive(self):
        response = self._login("STAFF@JNS.TEST", PASSWORD)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # -- rejected ----------------------------------------------------------

    def _assert_rejected(self, response):
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json(), {"detail": "Invalid email or password."})
        self.assertNotIn("user_id", self.client.session)

    def test_wrong_password_returns_401(self):
        self._assert_rejected(self._login("staff@jns.test", "wrong-password"))

    def test_unknown_email_returns_401(self):
        self._assert_rejected(self._login("nobody@jns.test", PASSWORD))

    def test_inactive_user_returns_401(self):
        self._assert_rejected(self._login("gone@jns.test", PASSWORD))

    def test_user_outside_jns_organisation_returns_401(self):
        # Correct credentials, but sp_get_login_user only returns the active
        # JNS Business Solutions organisation.
        self._assert_rejected(self._login("someone@charity.test", PASSWORD))

    def test_same_generic_message_for_unknown_and_wrong_password(self):
        # Neither response should reveal whether the email exists.
        unknown = self._login("nobody@jns.test", PASSWORD).json()
        wrong = self._login("staff@jns.test", "wrong-password").json()

        self.assertEqual(unknown, wrong)

    # -- validation --------------------------------------------------------

    def test_missing_fields_returns_400(self):
        response = self.client.post(URL, data={}, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        errors = response.json()

        self.assertIn("email", errors)
        self.assertIn("password", errors)

    def test_malformed_email_returns_400(self):
        response = self._login("not-an-email", PASSWORD)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.json())