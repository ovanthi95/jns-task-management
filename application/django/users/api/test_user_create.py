"""Tests for API 03 - POST /api/users

Test owner: Edward
Implementation owner: Manatka

Baseline cases from the implementation owner: 401, 403, 201 with safe
fields, password hashed in DB, duplicate email 400, unknown role 400,
missing fields 400, organisation taken from session not body.
Edward may add or adjust cases here.

MySQL only; procedures are loaded before the class-level transaction.
"""

from django.test import TestCase
from rest_framework import status

from data_access.sp_loader import load_stored_procedures
from users.models import Organisation, Role, User

URL = "/api/users"

VALID_BODY = {
    "first_name": "New",
    "last_name": "Person",
    "email": "new.person@jns.test",
    "password": "Str0ngPass!",
    "role_id": None,  # filled in setUpTestData once roles exist
    "availability": "Full-time",
}


class UserCreateApiTests(TestCase):
    @classmethod
    def setUpClass(cls):
        load_stored_procedures(
            "users/sp_get_session_user",
            "users/sp_create_user",
        )
        super().setUpClass()

    @classmethod
    def setUpTestData(cls):
        cls.admin_role = Role.objects.create(role_name="Admin")
        cls.manager_role = Role.objects.create(role_name="Manager")
        cls.employee_role = Role.objects.create(role_name="Employee")

        cls.org = cls._organisation("JNS Business Solutions")
        cls.other_org = cls._organisation("Unrelated Charity")

        cls.admin = cls._user(cls.org, "admin@jns.test", cls.admin_role)
        cls.manager = cls._user(cls.org, "manager@jns.test", cls.manager_role)

        cls.body = {**VALID_BODY, "role_id": cls.employee_role.role_id}

    @staticmethod
    def _organisation(name):
        return Organisation.objects.create(
            organisation_name=name,
            organisation_type="Accounting",
            email=f"info@{name.split()[0].lower()}.test",
            phone="09-000-0000",
            address="Auckland",
            status="Active",
        )

    @staticmethod
    def _user(org, email, role):
        return User.objects.create_user(
            email=email, organisation=org, role=role, password="Passw0rd!",
            first_name=email.split("@")[0].title(), last_name="Test", status="Active",
        )

    def _login_as(self, user):
        session = self.client.session
        session["user_id"] = user.user_id
        session.save()

    def _post(self, body):
        return self.client.post(URL, data=body, content_type="application/json")

    # -- authentication / authorisation -----------------------------------

    def test_no_session_returns_401(self):
        response = self._post(self.body)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_manager_returns_403(self):
        self._login_as(self.manager)

        response = self._post(self.body)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(User.objects.filter(email=self.body["email"]).exists())

    # -- success -----------------------------------------------------------

    def test_admin_creates_user_and_gets_safe_fields(self):
        self._login_as(self.admin)

        response = self._post(self.body)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        payload = response.json()

        self.assertEqual(payload["email"], "new.person@jns.test")
        self.assertEqual(payload["role_name"], "Employee")
        self.assertEqual(payload["status"], "Active")
        self.assertNotIn("password", payload)
        self.assertNotIn("password_hash", payload)

        created = User.objects.get(user_id=payload["user_id"])

        # Organisation came from the session, and the password was hashed
        # before it reached the procedure.
        self.assertEqual(created.organisation_id, self.org.organisation_id)
        self.assertNotEqual(created.password, self.body["password"])
        self.assertTrue(created.check_password(self.body["password"]))

    def test_organisation_in_body_is_ignored(self):
        self._login_as(self.admin)

        response = self._post({**self.body, "organisation_id": self.other_org.organisation_id})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created = User.objects.get(user_id=response.json()["user_id"])

        self.assertEqual(created.organisation_id, self.org.organisation_id)

    def test_availability_is_optional(self):
        self._login_as(self.admin)

        body = {k: v for k, v in self.body.items() if k != "availability"}
        response = self._post(body)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.json()["availability"])

    # -- validation --------------------------------------------------------

    def test_duplicate_email_in_organisation_returns_400(self):
        self._login_as(self.admin)

        response = self._post({**self.body, "email": "manager@jns.test"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.json())
        self.assertNotIn("Duplicate entry", str(response.content))

    def test_unknown_role_returns_400(self):
        self._login_as(self.admin)

        response = self._post({**self.body, "role_id": 999})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("role_id", response.json())
        self.assertNotIn("foreign key", str(response.content).lower())

    def test_missing_required_fields_returns_400(self):
        self._login_as(self.admin)

        response = self._post({"email": "only@jns.test"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        errors = response.json()

        for field in ("first_name", "last_name", "password", "role_id"):
            self.assertIn(field, errors)

    def test_short_password_returns_400(self):
        self._login_as(self.admin)

        response = self._post({**self.body, "password": "short"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.json())