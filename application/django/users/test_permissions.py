"""Regression tests for session and permission boundaries."""

from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient


def actor(*permissions, user_id=1, organisation_id=1, role_name="Employee"):
    return {
        "user_id": user_id,
        "organisation_id": organisation_id,
        "role_id": 1,
        "role_name": role_name,
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "permissions": list(permissions),
    }


class PermissionBoundaryTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("audit.api.history.get_authenticated_session_user")
    def test_history_requires_view_history(self, get_actor):
        get_actor.return_value = actor()
        response = self.client.get("/api/history")
        self.assertEqual(response.status_code, 403)

    @patch("users.api.workload.get_authenticated_session_user")
    def test_workload_requires_view_workload(self, get_actor):
        get_actor.return_value = actor()
        response = self.client.get("/api/workload")
        self.assertEqual(response.status_code, 403)

    @patch("users.api.role_management.get_authenticated_session_user")
    def test_roles_require_role_access(self, get_actor):
        get_actor.return_value = actor()
        response = self.client.get("/api/roles")
        self.assertEqual(response.status_code, 403)

    @patch("users.api.role_management.get_authenticated_session_user")
    def test_role_changes_require_manage_roles(self, get_actor):
        get_actor.return_value = actor("manage_users")
        response = self.client.post(
            "/api/roles",
            {"role_name": "Reviewer", "permission_codes": []},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
