"""Tests for PATCH /api/projects/:projectId."""

from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase
from rest_framework.test import APIClient

from projects.services.project_update_service import (
    InvalidAdminPassword,
    ProjectNotFound,
    ReactivationPasswordRequired,
)


class ProjectUpdateViewTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/projects/1"

        self.actor = {
            "user_id": 1,
            "organisation_id": 1,
            "email": "admin@example.com",
        }

        self.updated_project = {
            "project_id": 1,
            "project_name": "Updated Project",
            "description": "Updated description",
            "start_date": "2026-10-01",
            "end_date": "2026-12-31",
            "status": "Active",
        }

    def _login(self):
        session = self.client.session
        session["user_id"] = 1
        session.save()

    @patch("projects.api.project_update.get_authenticated_session_user")
    def test_patch_without_login_returns_401(self, mock_get_user):
        mock_get_user.return_value = None

        response = self.client.patch(
            self.url,
            {"project_name": "Updated Project"},
            format="json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["detail"], "Not authenticated.")

    @patch("projects.api.project_update.actor_has_permission")
    @patch("projects.api.project_update.get_authenticated_session_user")
    def test_patch_without_permission_returns_403(
        self,
        mock_get_user,
        mock_permission,
    ):
        self._login()

        mock_get_user.return_value = self.actor
        mock_permission.return_value = False

        response = self.client.patch(
            self.url,
            {"project_name": "Updated Project"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "Project editing permission required.",
        )

    @patch("projects.api.project_update.edit_project")
    @patch("projects.api.project_update.actor_has_permission")
    @patch("projects.api.project_update.get_authenticated_session_user")
    def test_project_can_be_updated(
        self,
        mock_get_user,
        mock_permission,
        mock_edit_project,
    ):
        self._login()

        mock_get_user.return_value = self.actor
        mock_permission.return_value = True
        mock_edit_project.return_value = self.updated_project

        response = self.client.patch(
            self.url,
            {
                "project_name": "Updated Project",
                "description": "Updated description",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["project_name"],
            "Updated Project",
        )

        mock_edit_project.assert_called_once_with(
            actor=self.actor,
            project_id=1,
            changes={
                "project_name": "Updated Project",
                "description": "Updated description",
            },
            admin_password=None,
        )

    @patch("projects.api.project_update.actor_has_permission")
    @patch("projects.api.project_update.get_authenticated_session_user")
    def test_empty_patch_returns_400(
        self,
        mock_get_user,
        mock_permission,
    ):
        self._login()

        mock_get_user.return_value = self.actor
        mock_permission.return_value = True

        response = self.client.patch(
            self.url,
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    @patch("projects.api.project_update.edit_project")
    @patch("projects.api.project_update.actor_has_permission")
    @patch("projects.api.project_update.get_authenticated_session_user")
    def test_project_not_found_returns_404(
        self,
        mock_get_user,
        mock_permission,
        mock_edit_project,
    ):
        self._login()

        mock_get_user.return_value = self.actor
        mock_permission.return_value = True
        mock_edit_project.side_effect = ProjectNotFound()

        response = self.client.patch(
            self.url,
            {"project_name": "Updated Project"},
            format="json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data["detail"],
            "Project not found.",
        )

    @patch("projects.api.project_update.edit_project")
    @patch("projects.api.project_update.actor_has_permission")
    @patch("projects.api.project_update.get_authenticated_session_user")
    def test_reopen_completed_project_without_password_returns_400(
        self,
        mock_get_user,
        mock_permission,
        mock_edit_project,
    ):
        self._login()

        mock_get_user.return_value = self.actor
        mock_permission.return_value = True
        mock_edit_project.side_effect = ReactivationPasswordRequired()

        response = self.client.patch(
            self.url,
            {"status": "Active"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("admin_password", response.data)

    @patch("projects.api.project_update.edit_project")
    @patch("projects.api.project_update.actor_has_permission")
    @patch("projects.api.project_update.get_authenticated_session_user")
    def test_reopen_completed_project_with_wrong_password_returns_403(
        self,
        mock_get_user,
        mock_permission,
        mock_edit_project,
    ):
        self._login()

        mock_get_user.return_value = self.actor
        mock_permission.return_value = True
        mock_edit_project.side_effect = InvalidAdminPassword()

        response = self.client.patch(
            self.url,
            {
                "status": "Active",
                "admin_password": "wrong-password",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn("admin_password", response.data)

    @patch("projects.api.project_update.edit_project")
    @patch("projects.api.project_update.actor_has_permission")
    @patch("projects.api.project_update.get_authenticated_session_user")
    def test_end_date_before_start_date_returns_400(
        self,
        mock_get_user,
        mock_permission,
        mock_edit_project,
    ):
        self._login()

        mock_get_user.return_value = self.actor
        mock_permission.return_value = True
        mock_edit_project.side_effect = DatabaseError(
            "End date cannot be before start date"
        )

        response = self.client.patch(
            self.url,
            {
                "start_date": "2026-10-10",
                "end_date": "2026-10-01",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("end_date", response.data)