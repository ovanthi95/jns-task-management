"""Focused tests for API 13 - GET /api/history."""

from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient


def actor(*permissions):
    return {
        "user_id": 1,
        "organisation_id": 1,
        "role_id": 1,
        "role_name": "Admin",
        "first_name": "Admin",
        "last_name": "User",
        "email": "admin@example.com",
        "permissions": list(permissions),
    }


class HistoryApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("audit.api.history.get_authenticated_session_user", return_value=None)
    def test_unauthenticated_request_returns_401(self, _actor):
        response = self.client.get("/api/history")
        self.assertEqual(response.status_code, 401)

    @patch("audit.api.history.get_authenticated_session_user")
    def test_missing_permission_returns_403(self, get_actor):
        get_actor.return_value = actor()
        response = self.client.get("/api/history")
        self.assertEqual(response.status_code, 403)

    @patch("audit.api.history.get_authenticated_session_user")
    def test_invalid_entity_type_returns_400(self, get_actor):
        get_actor.return_value = actor("view_history")
        response = self.client.get("/api/history?entity_type=Other")
        self.assertEqual(response.status_code, 400)

    @patch("audit.api.history.get_authenticated_session_user")
    def test_authorised_empty_history_returns_expected_shape(self, get_actor):
        get_actor.return_value = actor("view_history")
        response = self.client.get("/api/history?entity_type=User")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["items"], [])
        self.assertEqual(response.data["total"], 0)
        self.assertIn("changed_by_options", response.data)
