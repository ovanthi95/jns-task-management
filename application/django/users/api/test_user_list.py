"""Tests for API 02 - GET /api/users

Test owner: Edward
Implementation owner: Manatka

These are the implementation owner's baseline cases (success, 401, 403,
organisation isolation, empty list), followed by the test owner's additions
under "-- added by the test owner".

MySQL only: the endpoint calls stored procedures, which SQLite cannot run.
The procedures are loaded into the temporary test database by the shared
loader BEFORE the class-level transaction starts, because CREATE PROCEDURE
is DDL and would otherwise break Django's test transaction.
"""

from django.test import TestCase
from django.urls import Resolver404, resolve
from rest_framework import status

from data_access.sp_loader import load_stored_procedures
from users.models import Organisation, Role, User

URL = "/api/users"


class UserListApiTests(TestCase):
    @classmethod
    def setUpClass(cls):
        # Before super(): DDL must run outside the class-level atomic block.
        load_stored_procedures(
            "users/sp_get_session_user",
            "users/sp_get_users",
        )
        super().setUpClass()

    @classmethod
    def setUpTestData(cls):
        # Test data is created through the ORM; that is setup, not the API's
        # database operation, which goes through the stored procedure.
        cls.admin_role = Role.objects.create(role_name="Admin")
        cls.manager_role = Role.objects.create(role_name="Manager")
        cls.employee_role = Role.objects.create(role_name="Employee")

        # The seed defines five system roles. The baseline exercised three;
        # Intern and Volunteer are here so every seeded role is covered.
        cls.intern_role = Role.objects.create(role_name="Intern")
        cls.volunteer_role = Role.objects.create(role_name="Volunteer")

        # sp_get_session_user only accepts the active JNS organisation.
        cls.org = cls._organisation("JNS Business Solutions")
        cls.other_org = cls._organisation("Unrelated Charity")

        cls.admin = cls._user(cls.org, "admin@jns.test", cls.admin_role)
        cls.manager = cls._user(cls.org, "manager@jns.test", cls.manager_role)
        cls.employee = cls._user(cls.org, "worker@jns.test", cls.employee_role)
        cls.outsider = cls._user(cls.other_org, "someone@charity.test", cls.admin_role)

    @staticmethod
    def _organisation(name):
        return Organisation.objects.create(
            organisation_name=name,
            organisation_type="Accounting",
            email=f"info@{name.split()[0].lower()}.test",
            phone="09-000-0000",
            address="Auckland",
            status="Active",
        )

    @staticmethod
    def _user(org, email, role, **overrides):
        fields = {
            "email": email,
            "organisation": org,
            "role": role,
            "password": "Passw0rd!",
            "first_name": email.split("@")[0].title(),
            "last_name": "Test",
            "status": "Active",
        }
        fields.update(overrides)

        return User.objects.create_user(**fields)

    def _login_as(self, user):
        """Simulate the session API 01 creates, without going through login."""

        session = self.client.session
        session["user_id"] = user.user_id
        session.save()

    # -- authentication ----------------------------------------------------

    def test_no_session_returns_401(self):
        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_session_for_unknown_user_returns_401(self):
        session = self.client.session
        session["user_id"] = 999999
        session.save()

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # -- authorisation -----------------------------------------------------

    def test_employee_returns_403(self):
        self._login_as(self.employee)

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_returns_200(self):
        self._login_as(self.admin)

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_manager_returns_200(self):
        self._login_as(self.manager)

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # -- response shape and isolation -------------------------------------

    def test_lists_only_own_organisation_without_password(self):
        self._login_as(self.admin)

        response = self.client.get(URL)
        body = response.json()

        emails = {u["email"] for u in body}

        self.assertEqual(
            emails,
            {"admin@jns.test", "manager@jns.test", "worker@jns.test"},
        )
        self.assertNotIn("someone@charity.test", emails)

        first = body[0]

        self.assertEqual(
            set(first.keys()),
            {
                "user_id", "first_name", "last_name", "email",
                "role_id", "role_name", "availability", "status",
            },
        )
        self.assertNotIn("password_hash", first)
        self.assertNotIn("password", first)

    def test_role_name_is_joined(self):
        self._login_as(self.admin)

        response = self.client.get(URL)
        by_email = {u["email"]: u for u in response.json()}

        self.assertEqual(by_email["manager@jns.test"]["role_name"], "Manager")
        self.assertEqual(by_email["manager@jns.test"]["role_id"], self.manager_role.role_id)

    # -- added by the test owner ------------------------------------------
    #
    # The baseline refused one of the three non-privileged roles and accepted
    # the two privileged ones. The seed defines five roles, the procedure
    # states an ORDER BY and deliberately omits a status filter, and the
    # service decides authorisation differently from API 03. None of that was
    # covered. Each case below pins one of those decisions so that changing it
    # has to be a decision rather than an accident.

    def test_an_intern_cannot_list_users(self):
        intern = self._user(self.org, "intern@jns.test", self.intern_role)
        self._login_as(intern)

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_a_volunteer_cannot_list_users(self):
        volunteer = self._user(self.org, "volunteer@jns.test", self.volunteer_role)
        self._login_as(volunteer)

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_the_list_is_ordered_by_last_name_then_first_name(self):
        """sp_get_users ends in ORDER BY u.last_name, u.first_name, u.user_id.

        The ordering is in the procedure rather than in Python, so the client
        can render the list without sorting it. Nothing asserted it, which
        meant the ORDER BY could be dropped in a rewrite and every other test
        would still pass.
        """

        self._user(self.org, "zoe@jns.test", self.employee_role,
                   first_name="Zoe", last_name="Adams")
        self._user(self.org, "amy@jns.test", self.employee_role,
                   first_name="Amy", last_name="Adams")

        self._login_as(self.admin)

        body = self.client.get(URL).json()
        order = [(u["last_name"], u["first_name"]) for u in body]

        self.assertEqual(order, sorted(order))
        self.assertEqual(order[0], ("Adams", "Amy"))
        self.assertEqual(order[1], ("Adams", "Zoe"))

    def test_a_suspended_user_is_still_listed(self):
        """The procedure has no WHERE on status, and that is deliberate.

        A manager assigning work needs to see that an account exists and is
        suspended, rather than have it silently disappear from the list. The
        status field is returned so the client can mark it. If a status filter
        is ever added to sp_get_users, this test should fail and the change
        should be argued for rather than slipped in.
        """

        self._user(self.org, "suspended@jns.test", self.employee_role,
                   status="Suspended")

        self._login_as(self.admin)

        body = self.client.get(URL).json()
        by_email = {u["email"]: u for u in body}

        self.assertIn("suspended@jns.test", by_email)
        self.assertEqual(by_email["suspended@jns.test"]["status"], "Suspended")

    def test_configured_role_permissions_do_not_affect_this_endpoint(self):
        """Records a divergence between API 02 and API 03, it does not bless it.

        API 03 authorises through actor_has_permission(session_user,
        "manage_users"), which reads the configurable RBAC tables. API 02
        authorises through USER_LIST_ROLES, a frozenset of role names
        hard-coded in user_list_service.py, and never consults RBAC at all.

        So an administrator who reconfigures the Manager role and removes its
        permissions stops Managers creating users but does not stop them
        listing users, and a custom role granted "manage_users" can create a
        user it cannot then see in the list.

        This test asserts what the code does today, which is a 200. It is here
        so the inconsistency is visible in the suite rather than only in the
        source. If the team unifies the two endpoints on RBAC, this test
        should be changed to expect 403 in the same commit.
        """

        self.manager_role.permissions_configured = True
        self.manager_role.save(update_fields=["permissions_configured"])

        self._login_as(self.manager)

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_the_route_has_no_trailing_slash(self):
        """Playbook convention: no /api/v1 and no trailing slash.

        Resolved rather than requested, so the assertion is about the URL
        configuration itself and does not depend on the APPEND_SLASH setting.
        """

        self.assertTrue(resolve(URL))

        with self.assertRaises(Resolver404):
            resolve(URL + "/")
