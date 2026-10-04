"""Mock tests for API 12 - PATCH /api/users/:userId.

These tests cover the API/View layer without requiring MySQL
stored procedures.
"""

from unittest.mock import patch

from django.db import DatabaseError, IntegrityError
from django.test import TestCase
from rest_framework.test import APIClient


def make_admin():
    """Return an authenticated user with manage_users permission."""
    return {
        "user_id": 1,
        "organisation_id": 1,
        "role_id": 1,
        "role_name": "Admin",
        "first_name": "Admin",
        "last_name": "User",
        "email": "admin@jns.test",
        "permissions": ["manage_users"],
    }


def make_manager():
    """Return an authenticated user without manage_users permission."""
    return {
        "user_id": 2,
        "organisation_id": 1,
        "role_id": 2,
        "role_name": "Manager",
        "first_name": "Manager",
        "last_name": "User",
        "email": "manager@jns.test",
        "permissions": [],
    }


class UserUpdateMockTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/users/3"

    def set_session(self, user_id=1):
        session = self.client.session
        session["user_id"] = user_id
        session.save()

    # ---------------------------------------------------------
    # 1. No session -> 401
    # ---------------------------------------------------------
    def test_no_session_returns_401(self):
        response = self.client.patch(
            self.url,
            {"first_name": "Changed"},
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    # ---------------------------------------------------------
    # 2. Authentication succeeds, but View cannot resolve actor
    #    -> 401
    # ---------------------------------------------------------
    @patch("users.authentication.get_authenticated_session_user")
    @patch("users.api.user_update.get_authenticated_session_user")
    def test_invalid_session_user_returns_401(
        self,
        mock_view_get_user,
        mock_auth_get_user,
    ):
        mock_auth_get_user.return_value = make_admin()
        mock_view_get_user.return_value = None

        self.set_session()

        response = self.client.patch(
            self.url,
            {"first_name": "Changed"},
            format="json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {"detail": "Not authenticated."},
        )

    # ---------------------------------------------------------
    # 3. User does not have manage_users permission -> 403
    # ---------------------------------------------------------
    @patch("users.authentication.get_authenticated_session_user")
    @patch("users.api.user_update.get_authenticated_session_user")
    @patch("users.api.user_update.actor_has_permission")
    def test_user_without_permission_returns_403(
        self,
        mock_has_permission,
        mock_view_get_user,
        mock_auth_get_user,
    ):
        manager = make_manager()

        mock_auth_get_user.return_value = manager
        mock_view_get_user.return_value = manager
        mock_has_permission.return_value = False

        self.set_session(user_id=2)

        response = self.client.patch(
            self.url,
            {"first_name": "Changed"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {"detail": "User management permission required."},
        )

    # ---------------------------------------------------------
    # 4. Admin successfully updates another user -> 200
    # ---------------------------------------------------------
    @patch("users.authentication.get_authenticated_session_user")
    @patch("users.api.user_update.get_authenticated_session_user")
    @patch("users.api.user_update.actor_has_permission")
    @patch("users.api.user_update.edit_user")
    def test_admin_can_update_user(
        self,
        mock_edit_user,
        mock_has_permission,
        mock_view_get_user,
        mock_auth_get_user,
    ):
        admin = make_admin()

        mock_auth_get_user.return_value = admin
        mock_view_get_user.return_value = admin
        mock_has_permission.return_value = True

        mock_edit_user.return_value = {
            "user_id": 3,
            "first_name": "Janet",
            "last_name": "Worker",
            "email": "janet@jns.test",
            "role_name": "Employee",
            "availability": "Part-time",
            "status": "Active",
        }

        self.set_session()

        response = self.client.patch(
            self.url,
            {
                "first_name": "Janet",
                "email": "JANET@JNS.TEST",
                "availability": "Part-time",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["first_name"],
            "Janet",
        )
        self.assertEqual(
            response.data["email"],
            "janet@jns.test",
        )
        self.assertEqual(
            response.data["availability"],
            "Part-time",
        )

        mock_edit_user.assert_called_once_with(
            actor=admin,
            user_id=3,
            changes={
                "first_name": "Janet",
                "email": "janet@jns.test",
                "availability": "Part-time",
            },
        )

    # ---------------------------------------------------------
    # 5. Admin cannot deactivate own account -> 400
    # ---------------------------------------------------------
    @patch("users.authentication.get_authenticated_session_user")
    @patch("users.api.user_update.get_authenticated_session_user")
    @patch("users.api.user_update.actor_has_permission")
    def test_admin_cannot_deactivate_self(
        self,
        mock_has_permission,
        mock_view_get_user,
        mock_auth_get_user,
    ):
        admin = make_admin()

        mock_auth_get_user.return_value = admin
        mock_view_get_user.return_value = admin
        mock_has_permission.return_value = True

        self.set_session()

        response = self.client.patch(
            "/api/users/1",
            {"status": "Inactive"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("status", response.data)

    # ---------------------------------------------------------
    # 6. Target user does not exist -> 404
    # ---------------------------------------------------------
    @patch("users.authentication.get_authenticated_session_user")
    @patch("users.api.user_update.get_authenticated_session_user")
    @patch("users.api.user_update.actor_has_permission")
    @patch("users.api.user_update.edit_user")
    def test_user_not_found_returns_404(
        self,
        mock_edit_user,
        mock_has_permission,
        mock_view_get_user,
        mock_auth_get_user,
    ):
        admin = make_admin()

        mock_auth_get_user.return_value = admin
        mock_view_get_user.return_value = admin
        mock_has_permission.return_value = True

        mock_edit_user.side_effect = DatabaseError(
            "User not found"
        )

        self.set_session()

        response = self.client.patch(
            self.url,
            {"first_name": "Changed"},
            format="json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {"detail": "User not found."},
        )

    # ---------------------------------------------------------
    # 7. Duplicate email -> 400
    # ---------------------------------------------------------
    @patch("users.authentication.get_authenticated_session_user")
    @patch("users.api.user_update.get_authenticated_session_user")
    @patch("users.api.user_update.actor_has_permission")
    @patch("users.api.user_update.edit_user")
    def test_duplicate_email_returns_400(
        self,
        mock_edit_user,
        mock_has_permission,
        mock_view_get_user,
        mock_auth_get_user,
    ):
        admin = make_admin()

        mock_auth_get_user.return_value = admin
        mock_view_get_user.return_value = admin
        mock_has_permission.return_value = True

        mock_edit_user.side_effect = IntegrityError(
            1062,
            "Duplicate entry",
        )

        self.set_session()

        response = self.client.patch(
            self.url,
            {"email": "duplicate@jns.test"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data)
        self.assertEqual(
            response.data["email"],
            ["This email is already in use."],
        )

    # ---------------------------------------------------------
    # 8. Empty PATCH request -> 400
    # ---------------------------------------------------------
    @patch("users.authentication.get_authenticated_session_user")
    @patch("users.api.user_update.get_authenticated_session_user")
    @patch("users.api.user_update.actor_has_permission")
    def test_empty_update_returns_400(
        self,
        mock_has_permission,
        mock_view_get_user,
        mock_auth_get_user,
    ):
        admin = make_admin()

        mock_auth_get_user.return_value = admin
        mock_view_get_user.return_value = admin
        mock_has_permission.return_value = True

        self.set_session()

        response = self.client.patch(
            self.url,
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 400)