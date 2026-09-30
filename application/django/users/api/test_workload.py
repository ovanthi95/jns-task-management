"""Focused tests for workload reporting APIs."""

from unittest.mock import patch

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
