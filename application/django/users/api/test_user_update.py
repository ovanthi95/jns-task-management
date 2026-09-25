"""Integration tests for API 12 - PATCH /api/users/:userId."""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from data_access.sp_loader import load_stored_procedures
from users.models import Organisation, Role, User


class UserUpdateApiTests(TestCase):
    @classmethod
    def setUpClass(cls):
        load_stored_procedures(
            "users/sp_get_session_user",
            "users/sp_update_user",
        )
        super().setUpClass()

    def setUp(self):
        self.admin_role = Role.objects.create(role_name="Admin")
        self.manager_role = Role.objects.create(role_name="Manager")
        self.employee_role = Role.objects.create(role_name="Employee")

        self.org = self._organisation("JNS")
        self.other_org = self._organisation("Other")

        self.admin = self._user(
            self.org,
            "admin@jns.test",
            self.admin_role,
            "Admin",
            "User",
        )
        self.manager = self._user(
            self.org,
            "manager@jns.test",
            self.manager_role,
            "Manager",
            "User",
        )
        self.worker = self._user(
            self.org,
            "worker@jns.test",
            self.employee_role,
            "Jane",
            "Worker",
        )
        self.other_user = self._user(
            self.other_org,
            "other@example.test",
            self.employee_role,
            "Other",
            "User",
        )

        self.client = APIClient()
        self.url = f"/api/users/{self.worker.user_id}"

    def test_no_session_returns_401(self):
        response = self.client.patch(
            self.url,
            {"first_name": "Changed"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_admin_returns_403(self):
        self._login_as(self.manager)

        response = self.client.patch(
            self.url,
            {"first_name": "Changed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_user_fields(self):
        self._login_as(self.admin)

        response = self.client.patch(
            self.url,
            {
                "first_name": "Janet",
                "email": "JANET@JNS.TEST",
                "role_name": "Manager",
                "availability": "Part-time",
                "status": "Active",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Janet")
        self.assertEqual(response.data["email"], "janet@jns.test")
        self.assertEqual(response.data["role_name"], "Manager")
        self.assertEqual(response.data["availability"], "Part-time")

        self.worker.refresh_from_db()
        self.assertEqual(self.worker.role_id, self.manager_role.role_id)

    def test_admin_cannot_deactivate_self(self):
        self._login_as(self.admin)

        response = self.client.patch(
            f"/api/users/{self.admin.user_id}",
            {"status": "Inactive"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_cannot_change_own_role(self):
        self._login_as(self.admin)

        response = self.client.patch(
            f"/api/users/{self.admin.user_id}",
            {"role_name": "Manager"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_in_other_organisation_returns_404(self):
        self._login_as(self.admin)

        response = self.client.patch(
            f"/api/users/{self.other_user.user_id}",
            {"first_name": "Changed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_duplicate_email_returns_400(self):
        duplicate = self._user(
            self.org,
            "duplicate@jns.test",
            self.employee_role,
            "Dupe",
            "User",
        )
        self._login_as(self.admin)

        response = self.client.patch(
            self.url,
            {"email": duplicate.email},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def _login_as(self, user):
        session = self.client.session
        session["user_id"] = user.user_id
        session.save()

    @staticmethod
    def _organisation(name):
        return Organisation.objects.create(
            organisation_name=name,
            organisation_type="SME",
            email=f"{name.lower()}@example.test",
            phone="09-000-0000",
            address="Auckland",
            status="Active",
        )

    @staticmethod
    def _user(org, email, role, first_name, last_name):
        return User.objects.create_user(
            email=email,
            organisation=org,
            role=role,
            password="Passw0rd!",
            first_name=first_name,
            last_name=last_name,
            status="Active",
        )
