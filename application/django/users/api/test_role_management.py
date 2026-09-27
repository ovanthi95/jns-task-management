"""Integration tests for API 14 role management."""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from data_access.sp_loader import load_stored_procedures
from users.models import Organisation, Role, User


class RoleManagementApiTests(TestCase):
    @classmethod
    def setUpClass(cls):
        load_stored_procedures("users/sp_get_session_user")
        super().setUpClass()

    def setUp(self):
        self.admin_role = Role.objects.create(role_name="Admin")
        self.employee_role = Role.objects.create(role_name="Employee")
        self.org = Organisation.objects.create(
            organisation_name="JNS Business Solutions",
            organisation_type="SME",
            email="info@jns.test",
            phone="09-000-0000",
            address="Auckland",
            status="Active",
        )
        self.admin = User.objects.create_user(
            email="admin@jns.test",
            organisation=self.org,
            role=self.admin_role,
            password="Passw0rd!",
            first_name="Admin",
            last_name="User",
            status="Active",
        )
        self.employee = User.objects.create_user(
            email="employee@jns.test",
            organisation=self.org,
            role=self.employee_role,
            password="Passw0rd!",
            first_name="Employee",
            last_name="User",
            status="Active",
        )
        self.client = APIClient()

    def _login_as(self, user):
        session = self.client.session
        session["user_id"] = user.user_id
        session.save()

    def test_no_session_returns_401(self):
        response = self.client.get("/api/roles")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_list_permission_catalog(self):
        self._login_as(self.admin)
        response = self.client.get("/api/roles")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["permissions"])
        self.assertTrue(any(role["role_name"] == "Admin" for role in response.data["roles"]))

    def test_admin_can_create_custom_role(self):
        self._login_as(self.admin)
        response = self.client.post(
            "/api/roles",
            {
                "role_name": "Coordinator",
                "description": "Coordinates projects",
                "permission_codes": [
                    "view_all_projects",
                    "view_all_tasks",
                    "view_history",
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role_name"], "Coordinator")
        self.assertIn("view_history", response.data["permission_codes"])

    def test_employee_cannot_manage_roles(self):
        self._login_as(self.employee)
        response = self.client.post(
            "/api/roles",
            {"role_name": "Coordinator"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_role_is_protected(self):
        self._login_as(self.admin)
        response = self.client.patch(
            f"/api/roles/{self.admin_role.role_id}",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
