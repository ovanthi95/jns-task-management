"""Tests for API 05 - GET /api/projects

Test owner: Manatka
Implementation owner: Jesse

Cases encode the contract in playbook section 10.2: organisation scope,
role-based visibility (Admin all; Manager created-or-member; other roles
member only), empty list is 200 [], newest first.

Tests only. Failures against the visibility rules are reported to the
implementation owner, not fixed here (playbook section 6).

MySQL only; procedures are loaded before the class-level transaction.
"""

from django.test import TestCase
from rest_framework import status

from data_access.sp_loader import load_stored_procedures
from projects.models import Project, ProjectMember
from users.models import Organisation, Role, User

from unittest import expectedFailure

URL = "/api/projects"


class ProjectListApiTests(TestCase):
    @classmethod
    def setUpClass(cls):
        load_stored_procedures(
            "users/sp_get_session_user",
            "projects/sp_get_projects",
        )
        super().setUpClass()

    @classmethod
    def setUpTestData(cls):
        cls.admin_role = Role.objects.create(role_name="Admin")
        cls.manager_role = Role.objects.create(role_name="Manager")
        cls.employee_role = Role.objects.create(role_name="Employee")

        cls.org = cls._organisation("JNS Business Solutions")
        cls.other_org = cls._organisation("Unrelated Charity")

        cls.admin = cls._user(cls.org, "admin@jns.test", cls.admin_role)
        cls.manager = cls._user(cls.org, "manager@jns.test", cls.manager_role)
        cls.employee = cls._user(cls.org, "worker@jns.test", cls.employee_role)
        cls.outsider = cls._user(cls.other_org, "someone@charity.test", cls.admin_role)

        # Created in this order so "newest first" is testable.
        cls.p_manager_created = Project.objects.create(
            organisation=cls.org, project_name="Created by manager", created_by=cls.manager)
        cls.p_shared = Project.objects.create(
            organisation=cls.org, project_name="Shared project", created_by=cls.admin)
        cls.p_admin_only = Project.objects.create(
            organisation=cls.org, project_name="Admin only", created_by=cls.admin)
        cls.p_other_org = Project.objects.create(
            organisation=cls.other_org, project_name="Charity project", created_by=cls.outsider)

        ProjectMember.objects.create(project=cls.p_shared, user=cls.manager)
        ProjectMember.objects.create(project=cls.p_shared, user=cls.employee)

    @staticmethod
    def _organisation(name):
        return Organisation.objects.create(
            organisation_name=name, organisation_type="Accounting",
            email=f"info@{name.split()[0].lower()}.test", phone="09-000-0000",
            address="Auckland", status="Active",
        )

    @staticmethod
    def _user(org, email, role):
        return User.objects.create_user(
            email=email, organisation=org, role=role, password="Passw0rd!",
            first_name=email.split("@")[0].title(), last_name="Test", status="Active",
        )

    def _login_as(self, user):
        session = self.client.session
        session["user_id"] = user.user_id
        session.save()

    def _names(self, response):
        return [p["project_name"] for p in response.json()["projects"]]

    # -- authentication ----------------------------------------------------

    def test_no_session_returns_401(self):
        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # -- shape -------------------------------------------------------------

    def test_response_shape_and_fields(self):
        self._login_as(self.admin)

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()

        self.assertIn("projects", body)
        self.assertIsInstance(body["projects"], list)

        first = body["projects"][0]

        for field in ("project_id", "project_name", "status", "created_by", "created_at"):
            self.assertIn(field, first)

    # -- organisation isolation -------------------------------------------

    def test_admin_sees_all_projects_in_own_organisation_only(self):
        self._login_as(self.admin)

        names = self._names(self.client.get(URL))

        self.assertEqual(set(names), {"Created by manager", "Shared project", "Admin only"})
        self.assertNotIn("Charity project", names)

    def test_newest_first(self):
        self._login_as(self.admin)

        names = self._names(self.client.get(URL))

        self.assertEqual(names, ["Admin only", "Shared project", "Created by manager"])

    def test_empty_organisation_returns_200_and_empty_list(self):
        Project.objects.filter(organisation=self.org).delete()
        self._login_as(self.admin)

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"projects": []})

    # -- role visibility (playbook 10.2) -----------------------------------

    # DEFECT (reported to Jesse, 28 Sep 2026): sp_get_projects filters by
    # organisation only and does not receive the caller's user_id/role, so
    # Manager and Employee currently see every project in the organisation.
    # Playbook 10.2 requires Admin=all, Manager=created-or-member,
    # others=member-only. Remove expectedFailure once fixed.
    @expectedFailure
    def test_manager_sees_created_or_member_projects_only(self):
        self._login_as(self.manager)

        names = self._names(self.client.get(URL))

        self.assertEqual(set(names), {"Created by manager", "Shared project"})
        self.assertNotIn("Admin only", names)

    @expectedFailure
    def test_employee_sees_member_projects_only(self):
        self._login_as(self.employee)

        names = self._names(self.client.get(URL))

        self.assertEqual(names, ["Shared project"])