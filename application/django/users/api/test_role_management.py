"""Integration tests for API 14 role management."""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from data_access.sp_loader import load_stored_procedures
from users.models import Organisation, Role, User


class RoleManagementApiTests(TestCase):
    @classmethod
    def setUpClass(cls):
        load_stored_procedures("users/sp_get_session_user")
        super().setUpClass()

    def setUp(self):
        self.admin_role = Role.objects.create(role_name="Admin")
        self.employee_role = Role.objects.create(role_name="Employee")
        self.org = Organisation.objects.create(
            organisation_name="JNS Business Solutions",
            organisation_type="SME",
            email="info@jns.test",
            phone="09-000-0000",
            address="Auckland",
            status="Active",
        )
        self.admin = User.objects.create_user(
            email="admin@jns.test",
            organisation=self.org,
            role=self.admin_role,
            password="Passw0rd!",
            first_name="Admin",
            last_name="User",
            status="Active",
        )
        self.employee = User.objects.create_user(
            email="employee@jns.test",
            organisation=self.org,
            role=self.employee_role,
            password="Passw0rd!",
            first_name="Employee",
            last_name="User",
            status="Active",
        )
        self.client = APIClient()

    def _login_as(self, user):
        session = self.client.session
        session["user_id"] = user.user_id
        session.save()

    def test_no_session_returns_401(self):
        response = self.client.get("/api/roles")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_list_permission_catalog(self):
        self._login_as(self.admin)
        response = self.client.get("/api/roles")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["permissions"])
        self.assertTrue(any(role["role_name"] == "Admin" for role in response.data["roles"]))

    def test_admin_can_create_custom_role(self):
        self._login_as(self.admin)
        response = self.client.post(
            "/api/roles",
            {
                "role_name": "Coordinator",
                "description": "Coordinates projects",
                "permission_codes": [
                    "view_all_projects",
                    "view_all_tasks",
                    "view_history",
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role_name"], "Coordinator")
        self.assertIn("view_history", response.data["permission_codes"])

    def test_employee_cannot_manage_roles(self):
        self._login_as(self.employee)
        response = self.client.post(
            "/api/roles",
            {"role_name": "Coordinator"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_role_is_protected(self):
        self._login_as(self.admin)
        response = self.client.patch(
            f"/api/roles/{self.admin_role.role_id}",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------ test-owner additions (Manatka)
    # Numbers refer to the 22 required cases on the API 14 Trello card.

    def _create_role(self, name, codes=None, **extra):
        self._login_as(self.admin)
        body = {"role_name": name, "permission_codes": codes or [], **extra}
        return self.client.post("/api/roles", body, format="json")

    def _role_manager_user(self):
        """A non-Admin user whose custom role carries manage_roles."""
        created = self._create_role("Role Manager", ["manage_roles"])
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        role = Role.objects.get(role_id=created.data["role_id"])
        return User.objects.create_user(
            email="rolemanager@jns.test", organisation=self.org, role=role,
            password="Passw0rd!", first_name="Role", last_name="Manager", status="Active",
        )

    # -- GET (3, 4, 5, 6)

    def test_get_without_role_permission_returns_403(self):  # 3
        self._login_as(self.employee)
        response = self.client.get("/api/roles")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotIn("roles", response.data)  # 6: no data leaks with the refusal

    def test_get_returns_active_and_inactive_roles(self):  # 4
        Role.objects.create(role_name="Legacy", is_active=False)
        self._login_as(self.admin)
        response = self.client.get("/api/roles")
        by_name = {r["role_name"]: r for r in response.data["roles"]}
        self.assertTrue(by_name["Admin"]["is_active"])
        self.assertTrue(by_name["Admin"]["is_protected"])
        self.assertFalse(by_name["Legacy"]["is_active"])
        self.assertFalse(by_name["Legacy"]["is_protected"])

    def test_get_returns_permission_catalogue_shape(self):  # 5
        self._login_as(self.admin)
        response = self.client.get("/api/roles")
        codes = {p["code"] for p in response.data["permissions"]}
        self.assertIn("manage_roles", codes)
        self.assertIn("manage_users", codes)
        for item in response.data["permissions"]:
            for key in ("code", "label", "category", "display_order"):
                self.assertIn(key, item)

    def test_non_admin_with_manage_roles_permission_can_read(self):  # 2, 6 (permission based, not name based)
        manager = self._role_manager_user()
        self._login_as(manager)
        response = self.client.get("/api/roles")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # -- POST (8, 9, 10, 11, 12, 13)

    def test_duplicate_role_name_returns_400(self):  # 8
        self.assertEqual(self._create_role("Coordinator").status_code, status.HTTP_201_CREATED)
        response = self._create_role("coordinator")  # case-insensitive unique in MySQL
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("role_name", response.data)

    def test_blank_role_name_returns_400(self):  # 9
        for bad in ("", "   "):
            response = self._create_role(bad)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("role_name", response.data)
        response = self.client.post("/api/roles", {}, format="json")  # missing entirely
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_permission_code_returns_400_and_creates_nothing(self):  # 10
        response = self._create_role("Ghost", ["does_not_exist"])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("permission_codes", response.data)
        self.assertFalse(Role.objects.filter(role_name="Ghost").exists())

    def test_admin_role_name_cannot_be_recreated(self):  # 11
        for name in ("Admin", "admin", " ADMIN "):
            response = self._create_role(name)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("role_name", response.data)
        self.assertEqual(Role.objects.filter(role_name__iexact="admin").count(), 1)

    def test_unauthenticated_cannot_create(self):  # 12
        response = self.client.post("/api/roles", {"role_name": "X"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_created_role_persists_with_selected_permissions(self):  # 13
        created = self._create_role("Auditor", ["view_history", "view_all_tasks"], description="Read only")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        listing = self.client.get("/api/roles").data["roles"]
        auditor = next(r for r in listing if r["role_name"] == "Auditor")
        self.assertEqual(auditor["permission_codes"], ["view_all_tasks", "view_history"])
        self.assertEqual(auditor["description"], "Read only")
        self.assertTrue(auditor["is_active"])

    # -- PATCH (14 to 22)

    def test_update_name_and_description_returns_200(self):  # 14
        role_id = self._create_role("Temp").data["role_id"]
        response = self.client.patch(
            f"/api/roles/{role_id}", {"role_name": "Renamed", "description": "New text"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role_name"], "Renamed")
        self.assertEqual(response.data["description"], "New text")
        self.assertEqual(Role.objects.get(role_id=role_id).role_name, "Renamed")

    def test_permission_set_is_replaced_on_update(self):  # 15
        role_id = self._create_role("Shifter", ["view_history", "view_all_tasks"]).data["role_id"]
        response = self.client.patch(
            f"/api/roles/{role_id}", {"permission_codes": ["view_all_projects"]}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["permission_codes"], ["view_all_projects"])

    def test_unknown_role_returns_404(self):  # 16
        self._login_as(self.admin)
        response = self.client.patch("/api/roles/999999", {"description": "x"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_to_duplicate_name_returns_400(self):  # 17
        self._create_role("First")
        second_id = self._create_role("Second").data["role_id"]
        response = self.client.patch(f"/api/roles/{second_id}", {"role_name": "first"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("role_name", response.data)

    def test_admin_role_cannot_be_renamed_or_stripped(self):  # 18
        self._login_as(self.admin)
        for body in ({"role_name": "SuperUser"}, {"permission_codes": []}, {"description": "x"}):
            response = self.client.patch(f"/api/roles/{self.admin_role.role_id}", body, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, body)
        self.admin_role.refresh_from_db()
        self.assertEqual(self.admin_role.role_name, "Admin")

    def test_role_with_active_users_cannot_be_deactivated(self):  # 19
        self._login_as(self.admin)
        response = self.client.patch(
            f"/api/roles/{self.employee_role.role_id}", {"is_active": False}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("is_active", response.data)
        self.employee_role.refresh_from_db()
        self.assertTrue(self.employee_role.is_active)

    def test_role_without_active_users_can_be_deactivated(self):  # 19 (positive side)
        role_id = self._create_role("Unused").data["role_id"]
        response = self.client.patch(f"/api/roles/{role_id}", {"is_active": False}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_active"])

    def test_invalid_permission_code_on_update_returns_400(self):  # 20
        role_id = self._create_role("Patchy", ["view_history"]).data["role_id"]
        response = self.client.patch(
            f"/api/roles/{role_id}", {"permission_codes": ["nope"]}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("permission_codes", response.data)
        self.assertEqual(Role.objects.get(role_id=role_id).role_permissions.count(), 1)  # existing set untouched

    def test_unauthorised_cannot_update(self):  # 21
        role_id = self._create_role("Locked").data["role_id"]
        self._login_as(self.employee)
        response = self.client.patch(f"/api/roles/{role_id}", {"description": "x"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()
        response = self.client.patch(f"/api/roles/{role_id}", {"description": "x"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_keeps_existing_users(self):  # 22
        self._login_as(self.admin)
        response = self.client.patch(
            f"/api/roles/{self.employee_role.role_id}",
            {"description": "Renamed description", "permission_codes": ["view_all_tasks"]},
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(User.objects.filter(user_id=self.employee.user_id).exists())
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.role_id, self.employee_role.role_id)