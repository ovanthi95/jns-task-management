"""Tests for GET /api/projects/:projectId/members."""

from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient


class ProjectMembersViewTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/projects/1/members"
        self.actor = {
            "user_id": 1,
            "organisation_id": 1,
            "email": "admin@example.com",
        }

    def _login(self):
        session = self.client.session
        session["user_id"] = 1
        session.save()

    @patch("projects.api.project_members.get_authenticated_session_user")
    def test_get_without_login_returns_401(self, mock_get_user):
        mock_get_user.return_value = None

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["detail"], "Not authenticated.")

    @patch("projects.api.project_members.actor_has_permission")
    @patch("projects.api.project_members.get_authenticated_session_user")
    def test_get_without_permission_returns_403(
        self,
        mock_get_user,
        mock_permission,
    ):
        self._login()
        mock_get_user.return_value = self.actor
        mock_permission.return_value = False

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "Project editing permission required.",
        )

    @patch("projects.api.project_members.list_project_members")
    @patch("projects.api.project_members.get_authenticated_session_user")
    def test_get_project_members_returns_members(
        self,
        mock_get_user,
        mock_list_members,
    ):
        self._login()
        mock_get_user.return_value = self.actor
        mock_list_members.return_value = [
            {
                "user_id": 1,
                "first_name": "Admin",
                "last_name": "User",
                "role_name": "Admin",
                "status": "Active",
                "is_creator": 1,
            }
        ]

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["members"]), 1)
        self.assertEqual(response.data["members"][0]["is_creator"], 1)
        mock_list_members.assert_called_once_with(self.actor, 1)

    @patch("projects.api.project_members.list_project_members")
    @patch("projects.api.project_members.get_authenticated_session_user")
    def test_missing_project_returns_404(
        self,
        mock_get_user,
        mock_list_members,
    ):
        from projects.services.project_members_service import ProjectMembersNotFound

        self._login()
        mock_get_user.return_value = self.actor
        mock_list_members.side_effect = ProjectMembersNotFound()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["detail"], "Project not found.")
