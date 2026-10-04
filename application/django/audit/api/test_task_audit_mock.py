"""Mock tests for API 11 - GET /api/tasks/:taskId/audit.

These tests cover the API/View layer without requiring MySQL
stored procedures.
"""

from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from audit.services.task_audit_service import TaskAuditNotFound


def make_user():
    """Return a complete authenticated session user."""
    return {
        "user_id": 1,
        "organisation_id": 1,
        "role_id": 1,
        "role_name": "Employee",
        "first_name": "Member",
        "last_name": "User",
        "email": "member@jns.test",
        "permissions": [],
    }


class TaskAuditMockTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/tasks/101/audit"

    def set_session(self):
        session = self.client.session
        session["user_id"] = 1
        session.save()

    def test_no_session_returns_401(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)

    @patch("users.authentication.get_authenticated_session_user")
    @patch("audit.api.task_audit.list_task_audit")
    def test_authenticated_user_can_read_audit(
        self,
        mock_list_task_audit,
        mock_auth_get_user,
    ):
        mock_auth_get_user.return_value = make_user()

        audit_rows = [
            {
                "field_name": "status_id",
                "old_value": {"status_name": "New"},
                "new_value": {"status_name": "Completed"},
            },
            {
                "field_name": "title",
                "old_value": "Old title",
                "new_value": "New title",
            },
        ]

        mock_list_task_audit.return_value = audit_rows

        self.set_session()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, audit_rows)

        mock_list_task_audit.assert_called_once_with(
            actor_user_id=1,
            task_id=101,
        )

    @patch("users.authentication.get_authenticated_session_user")
    @patch("audit.api.task_audit.list_task_audit")
    def test_empty_audit_returns_200(
        self,
        mock_list_task_audit,
        mock_auth_get_user,
    ):
        mock_auth_get_user.return_value = make_user()
        mock_list_task_audit.return_value = []

        self.set_session()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

        mock_list_task_audit.assert_called_once_with(
            actor_user_id=1,
            task_id=101,
        )

    @patch("users.authentication.get_authenticated_session_user")
    @patch("audit.api.task_audit.list_task_audit")
    def test_task_not_found_returns_404(
        self,
        mock_list_task_audit,
        mock_auth_get_user,
    ):
        mock_auth_get_user.return_value = make_user()
        mock_list_task_audit.side_effect = TaskAuditNotFound()

        self.set_session()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {"detail": "Not found."},
        )

        mock_list_task_audit.assert_called_once_with(
            actor_user_id=1,
            task_id=101,
        )