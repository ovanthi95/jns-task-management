"""Integration tests for workload reporting."""

from datetime import date, timedelta

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from data_access.sp_loader import load_stored_procedures
from projects.models import Project, ProjectMember
from tasks.models import Priority, Task, TaskAssignee, TaskStatus, TaskType
from users.models import Organisation, Role, User


class WorkloadApiTests(TestCase):
    @classmethod
    def setUpClass(cls):
        load_stored_procedures(
            "users/sp_get_session_user",
            "users/sp_get_workload",
            "users/sp_get_user_workload_tasks",
        )
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
            availability="Full-time",
        )

        self.project = Project.objects.create(
            organisation=self.org,
            project_name="Client Work",
            status="Active",
            created_by=self.admin,
        )
        ProjectMember.objects.create(project=self.project, user=self.employee)

        task_type = TaskType.objects.create(type_name="General")
        status_row = TaskStatus.objects.create(status_name="In Progress")
        priority = Priority.objects.create(
            priority_name="High",
            priority_level=3,
        )

        self.task = Task.objects.create(
            project=self.project,
            task_type=task_type,
            status=status_row,
            priority=priority,
            title="Prepare report",
            due_date=date.today() - timedelta(days=1),
            estimated_hours=4,
            created_by=self.admin,
        )
        TaskAssignee.objects.create(
            task=self.task,
            user=self.employee,
            assigned_by=self.admin,
        )

        self.client = APIClient()

    def _login_as(self, user):
        session = self.client.session
        session["user_id"] = user.user_id
        session.save()

    def test_no_session_returns_401(self):
        response = self.client.get("/api/workload")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_employee_without_permission_returns_403(self):
        self._login_as(self.employee)
        response = self.client.get("/api/workload")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_view_workload_summary(self):
        self._login_as(self.admin)

        response = self.client.get("/api/workload")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        worker = next(
            item
            for item in response.data["users"]
            if item["user_id"] == self.employee.user_id
        )
        self.assertEqual(worker["active_tasks"], 1)
        self.assertEqual(worker["overdue_tasks"], 1)
        self.assertIn("Client Work", worker["current_projects"])

    def test_admin_can_view_user_workload_tasks(self):
        self._login_as(self.admin)

        response = self.client.get(
            f"/api/workload/users/{self.employee.user_id}/tasks"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["task_id"], self.task.task_id)
        self.assertEqual(response.data[0]["project_name"], "Client Work")

    def test_other_organisation_user_returns_404(self):
        other_org = Organisation.objects.create(
            organisation_name="Other",
            organisation_type="SME",
            email="other@example.test",
            phone="09-111-1111",
            address="Auckland",
            status="Active",
        )
        outsider = User.objects.create_user(
            email="outside@example.test",
            organisation=other_org,
            role=self.employee_role,
            password="Passw0rd!",
            first_name="Outside",
            last_name="User",
            status="Active",
        )

        self._login_as(self.admin)

        response = self.client.get(
            f"/api/workload/users/{outsider.user_id}/tasks"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
