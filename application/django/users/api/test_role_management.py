"""Focused tests for API 14 - role management."""

from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from users.models import Role


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


class RoleManagementApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("users.api.role_management.get_authenticated_session_user", return_value=None)
    def test_unauthenticated_roles_returns_401(self, _actor):
        response = self.client.get("/api/roles")
        self.assertEqual(response.status_code, 401)

    @patch("users.api.role_management.get_authenticated_session_user")
    def test_get_roles_with_manage_users_returns_200(self, get_actor):
        get_actor.return_value = actor("manage_users")
        response = self.client.get("/api/roles")
        self.assertEqual(response.status_code, 200)
        self.assertIn("roles", response.data)
        self.assertIn("permissions", response.data)

    @patch("users.api.role_management.get_authenticated_session_user")
    def test_create_role_with_manage_roles_persists(self, get_actor):
        get_actor.return_value = actor("manage_roles")
        response = self.client.post(
            "/api/roles",
            {
                "role_name": "Reviewer",
                "description": "Review access",
                "permission_codes": [],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Role.objects.filter(role_name="Reviewer").exists())

    @patch("users.api.role_management.get_authenticated_session_user")
    def test_protected_admin_name_cannot_be_created(self, get_actor):
        get_actor.return_value = actor("manage_roles")
        response = self.client.post(
            "/api/roles",
            {"role_name": "Admin", "permission_codes": []},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    @patch("users.api.role_management.get_authenticated_session_user")
    def test_unknown_role_returns_404(self, get_actor):
        get_actor.return_value = actor("manage_roles")
        response = self.client.patch(
            "/api/roles/999999",
            {"description": "Changed"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)



# ====================================================================== test owner (Manatka)
# The 22 required cases from the API 14 Trello card, in the same mocked-actor
# style as the class above. Real Role / User rows are used where the rule is
# about data (active users, persistence); the actor itself is mocked.

from users.models import Organisation, User  # noqa: E402


def _actor(*permissions, role_name="Custom", user_id=1):
    data = actor(*permissions)
    data["role_name"] = role_name
    data["user_id"] = user_id
    return data


@patch("users.api.role_management.get_authenticated_session_user")
class RoleManagementCardCasesTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_role = Role.objects.create(role_name="Admin")
        self.employee_role = Role.objects.create(role_name="Employee")
        self.org = Organisation.objects.create(
            organisation_name="JNS Business Solutions", organisation_type="SME",
            email="info@jns.test", phone="09-000-0000", address="Auckland", status="Active",
        )
        self.employee = User.objects.create_user(
            email="employee@jns.test", organisation=self.org, role=self.employee_role,
            password="Passw0rd!", first_name="Employee", last_name="User", status="Active",
        )

    def _create(self, get_actor, name, codes=None, **extra):
        get_actor.return_value = _actor("manage_roles")
        return self.client.post(
            "/api/roles", {"role_name": name, "permission_codes": codes or [], **extra}, format="json",
        )

    # -- GET (1 to 6)

    def test_01_unauthenticated_get_returns_401(self, get_actor):
        get_actor.return_value = None
        self.assertEqual(self.client.get("/api/roles").status_code, 401)

    def test_02_authorised_get_returns_200_for_manage_roles_holder(self, get_actor):
        get_actor.return_value = _actor("manage_roles")  # permission based, not Admin name
        self.assertEqual(self.client.get("/api/roles").status_code, 200)

    def test_03_get_without_permission_returns_403_and_no_data(self, get_actor):
        get_actor.return_value = _actor()  # no permissions
        response = self.client.get("/api/roles")
        self.assertEqual(response.status_code, 403)
        self.assertNotIn("roles", response.data)  # 6

    def test_04_active_and_inactive_roles_are_represented(self, get_actor):
        Role.objects.create(role_name="Legacy", is_active=False)
        get_actor.return_value = _actor("manage_roles")
        by_name = {r["role_name"]: r for r in self.client.get("/api/roles").data["roles"]}
        self.assertTrue(by_name["Admin"]["is_active"])
        self.assertTrue(by_name["Admin"]["is_protected"])
        self.assertFalse(by_name["Legacy"]["is_active"])
        self.assertFalse(by_name["Legacy"]["is_protected"])

    def test_05_permission_catalogue_shape(self, get_actor):
        get_actor.return_value = _actor("manage_roles")
        catalogue = self.client.get("/api/roles").data["permissions"]
        codes = {p["code"] for p in catalogue}
        self.assertIn("manage_roles", codes)
        self.assertIn("manage_users", codes)
        for item in catalogue:
            for key in ("code", "label", "category", "display_order"):
                self.assertIn(key, item)

    # -- POST (7 to 13)

    def test_07_valid_create_returns_201(self, get_actor):
        response = self._create(get_actor, "Coordinator", ["view_history"], description="Coordinates")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["role_name"], "Coordinator")
        self.assertEqual(response.data["permission_codes"], ["view_history"])

    def test_08_duplicate_name_returns_400(self, get_actor):
        self.assertEqual(self._create(get_actor, "Coordinator").status_code, 201)
        response = self._create(get_actor, "coordinator")  # MySQL collation is case-insensitive
        self.assertEqual(response.status_code, 400)
        self.assertIn("role_name", response.data)

    def test_09_blank_or_missing_name_returns_400(self, get_actor):
        for bad in ("", "   "):
            response = self._create(get_actor, bad)
            self.assertEqual(response.status_code, 400)
            self.assertIn("role_name", response.data)
        get_actor.return_value = _actor("manage_roles")
        self.assertEqual(self.client.post("/api/roles", {}, format="json").status_code, 400)

    def test_10_unknown_permission_code_returns_400_and_creates_nothing(self, get_actor):
        response = self._create(get_actor, "Ghost", ["does_not_exist"])
        self.assertEqual(response.status_code, 400)
        self.assertIn("permission_codes", response.data)
        self.assertFalse(Role.objects.filter(role_name="Ghost").exists())

    def test_11_admin_name_cannot_be_recreated_in_any_case(self, get_actor):
        for name in ("Admin", "admin", " ADMIN "):
            response = self._create(get_actor, name)
            self.assertEqual(response.status_code, 400, name)
            self.assertIn("role_name", response.data)
        self.assertEqual(Role.objects.filter(role_name__iexact="admin").count(), 1)

    def test_12_unauthorised_cannot_create(self, get_actor):
        get_actor.return_value = _actor("manage_users")  # related but not sufficient
        self.assertEqual(self.client.post("/api/roles", {"role_name": "X"}, format="json").status_code, 403)
        get_actor.return_value = None
        self.assertEqual(self.client.post("/api/roles", {"role_name": "X"}, format="json").status_code, 401)
        self.assertFalse(Role.objects.filter(role_name="X").exists())

    def test_13_created_role_persists_with_selected_permissions(self, get_actor):
        created = self._create(get_actor, "Auditor", ["view_history", "view_all_tasks"])
        self.assertEqual(created.status_code, 201)
        listing = self.client.get("/api/roles").data["roles"]
        auditor = next(r for r in listing if r["role_name"] == "Auditor")
        self.assertEqual(auditor["permission_codes"], ["view_all_tasks", "view_history"])
        self.assertEqual(Role.objects.get(role_name="Auditor").role_permissions.count(), 2)

    # -- PATCH (14 to 22)

    def _patch(self, get_actor, role_id, body):
        get_actor.return_value = _actor("manage_roles")
        return self.client.patch(f"/api/roles/{role_id}", body, format="json")

    def test_14_name_and_description_update_returns_200(self, get_actor):
        role_id = self._create(get_actor, "Temp").data["role_id"]
        response = self._patch(get_actor, role_id, {"role_name": "Renamed", "description": "New text"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["role_name"], "Renamed")
        self.assertEqual(Role.objects.get(role_id=role_id).description, "New text")

    def test_15_permission_set_is_replaced(self, get_actor):
        role_id = self._create(get_actor, "Shifter", ["view_history", "view_all_tasks"]).data["role_id"]
        response = self._patch(get_actor, role_id, {"permission_codes": ["view_all_projects"]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["permission_codes"], ["view_all_projects"])

    def test_16_unknown_role_returns_404(self, get_actor):
        self.assertEqual(self._patch(get_actor, 999999, {"description": "x"}).status_code, 404)

    def test_17_update_to_duplicate_name_returns_400(self, get_actor):
        self._create(get_actor, "First")
        second_id = self._create(get_actor, "Second").data["role_id"]
        response = self._patch(get_actor, second_id, {"role_name": "first"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("role_name", response.data)

    def test_18_admin_role_cannot_be_renamed_deactivated_or_stripped(self, get_actor):
        for body in ({"role_name": "SuperUser"}, {"is_active": False}, {"permission_codes": []}):
            response = self._patch(get_actor, self.admin_role.role_id, body)
            self.assertEqual(response.status_code, 400, body)
        self.admin_role.refresh_from_db()
        self.assertEqual(self.admin_role.role_name, "Admin")
        self.assertTrue(self.admin_role.is_active)

    def test_19_role_with_active_users_cannot_be_deactivated(self, get_actor):
        response = self._patch(get_actor, self.employee_role.role_id, {"is_active": False})
        self.assertEqual(response.status_code, 400)
        self.assertIn("is_active", response.data)
        self.employee_role.refresh_from_db()
        self.assertTrue(self.employee_role.is_active)

    def test_19b_role_without_active_users_can_be_deactivated(self, get_actor):
        role_id = self._create(get_actor, "Unused").data["role_id"]
        response = self._patch(get_actor, role_id, {"is_active": False})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["is_active"])

    def test_20_invalid_permission_code_on_update_returns_400(self, get_actor):
        role_id = self._create(get_actor, "Patchy", ["view_history"]).data["role_id"]
        response = self._patch(get_actor, role_id, {"permission_codes": ["nope"]})
        self.assertEqual(response.status_code, 400)
        self.assertIn("permission_codes", response.data)
        self.assertEqual(Role.objects.get(role_id=role_id).role_permissions.count(), 1)

    def test_21_unauthorised_cannot_update(self, get_actor):
        role_id = self._create(get_actor, "Locked").data["role_id"]
        get_actor.return_value = _actor("manage_users")
        self.assertEqual(self.client.patch(f"/api/roles/{role_id}", {"description": "x"}, format="json").status_code, 403)
        get_actor.return_value = None
        self.assertEqual(self.client.patch(f"/api/roles/{role_id}", {"description": "x"}, format="json").status_code, 401)

    def test_22_update_keeps_existing_users(self, get_actor):
        response = self._patch(
            get_actor, self.employee_role.role_id,
            {"description": "Updated", "permission_codes": ["view_all_tasks"]},
        )
        self.assertEqual(response.status_code, 200)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.role_id, self.employee_role.role_id)