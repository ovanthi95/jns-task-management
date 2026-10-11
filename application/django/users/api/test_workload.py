"""Focused tests for workload reporting APIs."""

from unittest.mock import patch

from users.services.workload_service import list_user_workload_tasks

from django.test import TestCase
from rest_framework.test import APIClient


def actor(*permissions):
    return {
        "user_id": 1,
        "organisation_id": 1,
        "role_id": 1,
        "role_name": "Manager",
        "first_name": "Manager",
        "last_name": "User",
        "email": "manager@example.com",
        "permissions": list(permissions),
    }


class WorkloadApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("users.api.workload.get_authenticated_session_user", return_value=None)
    def test_unauthenticated_workload_returns_401(self, _actor):
        response = self.client.get("/api/workload")
        self.assertEqual(response.status_code, 401)

    @patch("users.api.workload.get_authenticated_session_user")
    def test_missing_permission_returns_403(self, get_actor):
        get_actor.return_value = actor()
        response = self.client.get("/api/workload")
        self.assertEqual(response.status_code, 403)

    @patch("users.api.workload.list_workload", return_value=[])
    @patch("users.api.workload.get_authenticated_session_user")
    def test_authorised_workload_returns_summary(self, get_actor, _list):
        get_actor.return_value = actor("view_workload")
        response = self.client.get("/api/workload")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["due_soon_days"], 7)
        self.assertEqual(response.data["users"], [])

    @patch("users.api.workload.list_user_workload_tasks", return_value=[])
    @patch("users.api.workload.get_authenticated_session_user")
    def test_authorised_user_drilldown_returns_tasks(self, get_actor, _list):
        get_actor.return_value = actor("view_workload")
        response = self.client.get("/api/workload/users/7/tasks")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])


class WorkloadScopeTests(TestCase):
    @patch("users.services.workload_service.get_user_workload", return_value=[{"user_id": 7}])
    @patch("users.services.workload_service.get_workload")
    def test_user_without_view_all_tasks_gets_only_own_workload(
        self, get_all, get_user
    ):
        actor_data = actor("view_workload")
        actor_data["user_id"] = 7

        from users.services.workload_service import list_workload

        rows = list_workload(actor=actor_data)

        get_user.assert_called_once_with(1, 7)
        get_all.assert_not_called()
        self.assertEqual(rows, [{"user_id": 7, "current_projects": []}])

    @patch("users.services.workload_service.get_workload", return_value=[{"user_id": 7}])
    @patch("users.services.workload_service.get_user_workload")
    def test_user_with_view_all_tasks_gets_team_workload(
        self, get_user, get_all
    ):
        actor_data = actor("view_workload", "view_all_tasks")

        from users.services.workload_service import list_workload

        rows = list_workload(actor=actor_data)

        get_all.assert_called_once_with(1)
        get_user.assert_not_called()
        self.assertEqual(rows, [{"user_id": 7, "current_projects": []}])
