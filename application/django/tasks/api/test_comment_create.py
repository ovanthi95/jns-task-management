"""Integration tests for API 09 - POST /api/tasks/:taskId/comments."""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from data_access.sp_loader import load_stored_procedures
from projects.models import Project, ProjectMember
from tasks.models import Comment, Priority, Task, TaskStatus, TaskType
from users.models import Organisation, Role, User


class TaskCommentApiTests(TestCase):
    @classmethod
    def setUpClass(cls):
        load_stored_procedures(
            "users/sp_get_session_user",
            "tasks/sp_get_task_access",
            "tasks/sp_add_comment",
        )
        super().setUpClass()

    def setUp(self):
        self.role = Role.objects.create(role_name="Employee")
        self.org = Organisation.objects.create(
            organisation_name="JNS",
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
        ProjectMember.objects.create(
            project=self.project,
            user=self.member,
        )

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

        self.client = APIClient()
        self.url = f"/api/tasks/{self.task.task_id}/comments"

    def test_no_session_returns_401(self):
        response = self.client.post(
            self.url,
            {"comment_text": "Hello"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_project_member_can_add_comment(self):
        self._login_as(self.member)

        response = self.client.post(
            self.url,
            {"comment_text": "Waiting for documents."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["comment_text"], "Waiting for documents.")
        self.assertEqual(response.data["user_id"], self.member.user_id)
        self.assertTrue(
            Comment.objects.filter(
                task=self.task,
                user=self.member,
                comment_text="Waiting for documents.",
            ).exists()
        )

    def test_blank_comment_returns_400(self):
        self._login_as(self.member)

        response = self.client.post(
            self.url,
            {"comment_text": "   "},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Comment.objects.exists())

    def test_non_member_gets_404(self):
        self._login_as(self.outsider)

        response = self.client.post(
            self.url,
            {"comment_text": "Should not be added"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(Comment.objects.exists())

    def test_unknown_task_returns_404(self):
        self._login_as(self.member)

        response = self.client.post(
            "/api/tasks/999999/comments",
            {"comment_text": "Missing task"},
            format="json",
        )

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
