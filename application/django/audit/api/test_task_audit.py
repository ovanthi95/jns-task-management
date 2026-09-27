"""Integration tests for API 11 - GET /api/tasks/:taskId/audit."""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from data_access.sp_loader import load_stored_procedures
from projects.models import Project, ProjectMember
from tasks.models import Priority, Task, TaskHistory, TaskStatus, TaskType
from users.models import Organisation, Role, User


class TaskAuditApiTests(TestCase):
    @classmethod
    def setUpClass(cls):
        load_stored_procedures(
            "users/sp_get_session_user",
            "tasks/sp_get_task_access",
            "audit/sp_get_task_audit",
        )
        super().setUpClass()

    def setUp(self):
        self.role = Role.objects.create(role_name="Employee")
        self.org = Organisation.objects.create(
            organisation_name="JNS Business Solutions",
            organisation_type="SME",
            email="info@jns.test",
            phone="09-000-0000",
            address="Auckland",
            status="Active",
        )
        self.member = self._user("member@jns.test", "Member", "User")
        self.outsider = self._user("outsider@jns.test", "Outside", "User")

        self.project = Project.objects.create(
            organisation=self.org,
            project_name="Client Work",
            created_by=self.member,
        )
        ProjectMember.objects.create(project=self.project, user=self.member)

        task_type = TaskType.objects.create(type_name="Accounting")
        task_status = TaskStatus.objects.create(status_name="New")
        priority = Priority.objects.create(
            priority_name="High",
            priority_level=3,
        )
        self.task = Task.objects.create(
            project=self.project,
            task_type=task_type,
            status=task_status,
            priority=priority,
            title="Prepare report",
            created_by=self.member,
        )

        TaskHistory.objects.create(
            task=self.task,
            changed_by=self.member,
            field_name="title",
            old_value="Old title",
            new_value="New title",
        )
        TaskHistory.objects.create(
            task=self.task,
            changed_by=self.member,
            field_name="status_id",
            old_value={"status_name": "New"},
            new_value={"status_name": "Completed"},
        )

        self.client = APIClient()
        self.url = f"/api/tasks/{self.task.task_id}/audit"

    def test_no_session_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_project_member_can_read_audit(self):
        self._login_as(self.member)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["field_name"], "status_id")
        self.assertEqual(
            response.data[0]["new_value"],
            {"status_name": "Completed"},
        )

    def test_non_member_gets_404(self):
        self._login_as(self.outsider)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unknown_task_returns_404(self):
        self._login_as(self.member)
        response = self.client.get("/api/tasks/999999/audit")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def _login_as(self, user):
        session = self.client.session
        session["user_id"] = user.user_id
        session.save()

    def _user(self, email, first_name, last_name):
        return User.objects.create_user(
            email=email,
            organisation=self.org,
            role=self.role,
            password="Passw0rd!",
            first_name=first_name,
            last_name=last_name,
            status="Active",
        )
