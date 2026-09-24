"""Tests for API 02 - GET /api/users

Test owner: Edward
Implementation owner: Manatka

These are the implementation owner's baseline cases (success, 401, 403,
organisation isolation, empty list). Edward may add or adjust cases here.

MySQL only: the endpoint calls stored procedures, which SQLite cannot run.
The procedures are loaded into the temporary test database by the shared
loader BEFORE the class-level transaction starts, because CREATE PROCEDURE
is DDL and would otherwise break Django's test transaction.
"""

from django.test import TestCase
from rest_framework import status

from data_access.sp_loader import load_stored_procedures
from users.models import Organisation, Role, User

URL = "/api/users"


class UserListApiTests(TestCase):
    @classmethod
    def setUpClass(cls):
        # Before super(): DDL must run outside the class-level atomic block.
        load_stored_procedures(
            "users/sp_get_session_user",
            "users/sp_get_users",
        )
        super().setUpClass()

    @classmethod
    def setUpTestData(cls):
        # Test data is created through the ORM; that is setup, not the API's
        # database operation, which goes through the stored procedure.
        cls.admin_role = Role.objects.create(role_name="Admin")
        cls.manager_role = Role.objects.create(role_name="Manager")
        cls.employee_role = Role.objects.create(role_name="Employee")

        # sp_get_session_user only accepts the active JNS organisation.
        cls.org = cls._organisation("JNS Business Solutions")
        cls.other_org = cls._organisation("Unrelated Charity")

        cls.admin = cls._user(cls.org, "admin@jns.test", cls.admin_role)
        cls.manager = cls._user(cls.org, "manager@jns.test", cls.manager_role)
        cls.employee = cls._user(cls.org, "worker@jns.test", cls.employee_role)
        cls.outsider = cls._user(cls.other_org, "someone@charity.test", cls.admin_role)

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
            email=email,
            organisation=org,
            role=role,
            password="Passw0rd!",
            first_name=email.split("@")[0].title(),
            last_name="Test",
            status="Active",
        )

    def _login_as(self, user):
        """Simulate the session API 01 creates, without going through login."""

        session = self.client.session
        session["user_id"] = user.user_id
        session.save()

    # -- authentication ----------------------------------------------------

    def test_no_session_returns_401(self):
        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_session_for_unknown_user_returns_401(self):
        session = self.client.session
        session["user_id"] = 999999
        session.save()

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # -- authorisation -----------------------------------------------------

    def test_employee_returns_403(self):
        self._login_as(self.employee)

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_returns_200(self):
        self._login_as(self.admin)

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_manager_returns_200(self):
        self._login_as(self.manager)

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # -- response shape and isolation -------------------------------------

    def test_lists_only_own_organisation_without_password(self):
        self._login_as(self.admin)

        response = self.client.get(URL)
        body = response.json()

        emails = {u["email"] for u in body}

        self.assertEqual(
            emails,
            {"admin@jns.test", "manager@jns.test", "worker@jns.test"},
        )
        self.assertNotIn("someone@charity.test", emails)

        first = body[0]

        self.assertEqual(
            set(first.keys()),
            {
                "user_id", "first_name", "last_name", "email",
                "role_id", "role_name", "availability", "status",
            },
        )
        self.assertNotIn("password_hash", first)
        self.assertNotIn("password", first)

    def test_role_name_is_joined(self):
        self._login_as(self.admin)

        response = self.client.get(URL)
        by_email = {u["email"]: u for u in response.json()}

        self.assertEqual(by_email["manager@jns.test"]["role_name"], "Manager")
        self.assertEqual(by_email["manager@jns.test"]["role_id"], self.manager_role.role_id)