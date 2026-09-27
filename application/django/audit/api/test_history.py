"""Integration tests for API 13 - GET /api/history."""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from audit.models import AuditLog
from data_access.sp_loader import load_stored_procedures
from projects.models import Project
from users.models import Organisation, Role, User


class HistoryApiTests(TestCase):
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
        self.project = Project.objects.create(
            organisation=self.org,
            project_name="Client Work",
            status="Active",
            created_by=self.admin,
        )
        AuditLog.objects.create(
            organisation=self.org,
            user=self.admin,
            action="Created",
            entity_type="Project",
            entity_id=self.project.project_id,
            entity_name=self.project.project_name,
            description="Project created.",
        )
        self.client = APIClient()

    def _login_as(self, user):
        session = self.client.session
        session["user_id"] = user.user_id
        session.save()

    def test_no_session_returns_401(self):
        response = self.client.get("/api/history?entity_type=Project")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_view_project_history(self):
        self._login_as(self.admin)
        response = self.client.get("/api/history?entity_type=Project")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["items"][0]["entity_name"], "Client Work")
        self.assertEqual(response.data["current_items"][0]["entity_name"], "Client Work")

    def test_employee_without_history_permission_returns_403(self):
        self._login_as(self.employee)
        response = self.client.get("/api/history?entity_type=Project")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_entity_type_returns_400(self):
        self._login_as(self.admin)
        response = self.client.get("/api/history?entity_type=Unknown")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
