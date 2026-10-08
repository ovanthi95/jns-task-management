"""Tests for API 05 - GET /api/projects

Test owner: Jessie
Keep automated tests for this endpoint in this file.
"""

from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from projects.services.project_list_service import ProjectListPermissionError


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
        "permissions": ["view_all_projects"],
    }


class ProjectListAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/projects"

    def test_get_projects_without_login_returns_401(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {"detail": "Authentication required."},
        )

    @patch(
        "users.authentication.get_authenticated_session_user",
        return_value=None,
    )
    @patch(
        "projects.api.project_list.get_authenticated_session_user",
        return_value=None,
    )
    def test_invalid_session_user_returns_401(
        self,
        mock_project_get_user,
        mock_auth_get_user,
    ):
        session = self.client.session
        session["user_id"] = 1
        session.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)

    @patch("users.authentication.get_authenticated_session_user")
    @patch("projects.api.project_list.get_authenticated_session_user")
    @patch("projects.api.project_list.get_project_list")
    def test_get_projects_returns_200(
        self,
        mock_get_project_list,
        mock_project_get_user,
        mock_auth_get_user,
    ):
        current_user = make_user()

        projects = [
            {
                "project_id": 1,
                "project_name": "Project A",
            },
            {
                "project_id": 2,
                "project_name": "Project B",
            },
        ]

        mock_auth_get_user.return_value = current_user
        mock_project_get_user.return_value = current_user
        mock_get_project_list.return_value = projects

        session = self.client.session
        session["user_id"] = 1
        session.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"projects": projects},
        )

        mock_get_project_list.assert_called_once_with(current_user)

    @patch("users.authentication.get_authenticated_session_user")
    @patch("projects.api.project_list.get_authenticated_session_user")
    @patch("projects.api.project_list.get_project_list")
    def test_permission_error_returns_403(
        self,
        mock_get_project_list,
        mock_project_get_user,
        mock_auth_get_user,
    ):
        current_user = make_user()

        mock_auth_get_user.return_value = current_user
        mock_project_get_user.return_value = current_user
        mock_get_project_list.side_effect = ProjectListPermissionError(
            "Permission denied."
        )

        session = self.client.session
        session["user_id"] = 1
        session.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {"detail": "Permission denied."},
        )