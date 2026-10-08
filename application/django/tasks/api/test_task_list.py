"""Tests for API 07 - GET /api/projects/:projectId/tasks

Test owner: Jessie
Keep automated tests for this endpoint in this file.
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from tasks.services.exceptions import ProjectNotVisible


def make_user():
    """Return a complete authenticated session user."""
    return {
        "user_id": 1,
        "organisation_id": 1,
        "role_id": 1,
        "role_name": "Admin",
        "first_name": "Admin",
        "last_name": "User",
        "email": "admin@example.com",
        "permissions": [],
    }


def make_task():
    """Return one task in the shape expected by TaskSerializer."""
    return {
        "task_id": 101,
        "project_id": 1,
        "task_type_id": 1,
        "task_type_name": "Accounting",
        "status_id": 1,
        "status_name": "To Do",
        "priority_id": 1,
        "priority_name": "High",
        "title": "Prepare monthly report",
        "description": "Prepare the monthly accounting report.",
        "start_date": "2026-10-01",
        "due_date": "2026-10-10",
        "estimated_hours": Decimal("4.50"),
        "actual_hours": Decimal("2.00"),
        "assignees": [
            {
                "user_id": 2,
                "first_name": "Test",
                "last_name": "User",
                "assignment_role": "Assignee",
            }
        ],
        "created_by_id": 1,
        "created_at": datetime(2026, 10, 1, 10, 0, 0),
        "updated_at": datetime(2026, 10, 2, 10, 0, 0),
    }


class TaskListAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/projects/1/tasks"

    def set_session(self):
        session = self.client.session
        session["user_id"] = 1
        session.save()

    def test_get_tasks_without_login_returns_401(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)

    @patch("users.authentication.get_authenticated_session_user")
    @patch("tasks.api.task_list.task_list_service.list_project_tasks")
    def test_get_tasks_returns_200(
        self,
        mock_list_tasks,
        mock_auth_get_user,
    ):
        current_user = make_user()

        mock_auth_get_user.return_value = current_user
        mock_list_tasks.return_value = [make_task()]

        self.set_session()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["task_id"], 101)
        self.assertEqual(
            response.data[0]["title"],
            "Prepare monthly report",
        )

    @patch("users.authentication.get_authenticated_session_user")
    @patch("tasks.api.task_list.task_list_service.list_project_tasks")
    def test_empty_task_list_returns_200(
        self,
        mock_list_tasks,
        mock_auth_get_user,
    ):
        mock_auth_get_user.return_value = make_user()
        mock_list_tasks.return_value = []

        self.set_session()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    @patch("users.authentication.get_authenticated_session_user")
    def test_invalid_status_filter_returns_400(
        self,
        mock_auth_get_user,
    ):
        mock_auth_get_user.return_value = make_user()

        self.set_session()

        response = self.client.get(
            self.url,
            {"status_id": "abc"},
        )

        self.assertEqual(response.status_code, 400)

    @patch("users.authentication.get_authenticated_session_user")
    def test_invalid_priority_filter_returns_400(
        self,
        mock_auth_get_user,
    ):
        mock_auth_get_user.return_value = make_user()

        self.set_session()

        response = self.client.get(
            self.url,
            {"priority_id": "abc"},
        )

        self.assertEqual(response.status_code, 400)

    @patch("users.authentication.get_authenticated_session_user")
    def test_invalid_assignee_filter_returns_400(
        self,
        mock_auth_get_user,
    ):
        mock_auth_get_user.return_value = make_user()

        self.set_session()

        response = self.client.get(
            self.url,
            {"assignee_id": "abc"},
        )

        self.assertEqual(response.status_code, 400)

    @patch("users.authentication.get_authenticated_session_user")
    @patch("tasks.api.task_list.task_list_service.list_project_tasks")
    def test_project_not_visible_returns_404(
        self,
        mock_list_tasks,
        mock_auth_get_user,
    ):
        mock_auth_get_user.return_value = make_user()
        mock_list_tasks.side_effect = ProjectNotVisible()

        self.set_session()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {"detail": "Not found."},
        )

    @patch("users.authentication.get_authenticated_session_user")
    @patch("tasks.api.task_list.task_list_service.list_project_tasks")
    def test_filters_are_passed_to_service(
        self,
        mock_list_tasks,
        mock_auth_get_user,
    ):
        mock_auth_get_user.return_value = make_user()
        mock_list_tasks.return_value = []

        self.set_session()

        response = self.client.get(
            self.url,
            {
                "status_id": "2",
                "priority_id": "3",
                "assignee_id": "4",
            },
        )

        self.assertEqual(response.status_code, 200)

        call_kwargs = mock_list_tasks.call_args.kwargs

        self.assertEqual(call_kwargs["project_id"], 1)
        self.assertEqual(call_kwargs["status_id"], 2)
        self.assertEqual(call_kwargs["priority_id"], 3)
        self.assertEqual(call_kwargs["assignee_id"], 4)
        self.assertIsNotNone(call_kwargs["user"])