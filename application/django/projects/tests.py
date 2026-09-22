"""Tests for API 04 and API 05.

    API 04  POST /api/projects
    API 05  GET  /api/projects

Run these tests against SQLite, never against RDS.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import Organisation, Role, User

from .models import Project, ProjectMember


class ProjectApiTests(TestCase):

    def setUp(self):
        self.admin_role = Role.objects.create(role_name="Admin")
        self.manager_role = Role.objects.create(role_name="Manager")
        self.employee_role = Role.objects.create(role_name="Employee")

        self.org = self._organisation("JNS Business Solutions")
        self.other_org = self._organisation("Other Organisation")

        self.admin = self._user(
            self.org,
            "admin@jns.test",
            self.admin_role,
        )

        self.manager = self._user(
            self.org,
            "manager@jns.test",
            self.manager_role,
        )

        self.employee = self._user(
            self.org,
            "employee@jns.test",
            self.employee_role,
        )

        self.other_manager = self._user(
            self.other_org,
            "manager@other.test",
            self.manager_role,
        )

        self.url = reverse("projects")

        self.client = APIClient()
        self.client.force_authenticate(user=self.manager)

    # ----------------------------------------------------------- helpers

    def _organisation(self, name):
        return Organisation.objects.create(
            organisation_name=name,
            organisation_type="SME",
            email="contact@example.test",
            phone="000",
            address="1 Test Street",
            status="Active",
        )

    def _user(self, organisation, email, role):
        return User.objects.create_user(
            email=email,
            organisation=organisation,
            role=role,
            password="not-a-real-password",
            first_name="Test",
            last_name="User",
        )

    def _payload(self, **overrides):
        payload = {
            "project_name": "Annual Accounts 2026",
            "description": "Prepare annual accounts.",
            "status": "Active",
            "start_date": "2026-10-01",
            "end_date": "2026-12-01",
            "member_ids": [self.employee.pk],
        }

        payload.update(overrides)

        return payload

    def _project(self, creator, name):
        return Project.objects.create(
            organisation=creator.organisation,
            project_name=name,
            created_by=creator,
        )

    # ---------------------------------------------------- API 04 creation

    def test_manager_can_create_project(self):
        response = self.client.post(
            self.url,
            self._payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(Project.objects.count(), 1)

    def test_admin_can_create_project(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            self.url,
            self._payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

    def test_employee_cannot_create_project(self):
        self.client.force_authenticate(user=self.employee)

        response = self.client.post(
            self.url,
            self._payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(Project.objects.count(), 0)

    def test_create_uses_authenticated_users_organisation_and_identity(self):
        response = self.client.post(
            self.url,
            self._payload(
                organisation_id=self.other_org.pk,
                created_by=self.other_manager.pk,
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        project = Project.objects.get()

        self.assertEqual(
            project.organisation_id,
            self.manager.organisation_id,
        )
        self.assertEqual(
            project.created_by_id,
            self.manager.pk,
        )

    def test_creator_becomes_project_member(self):
        self.client.post(
            self.url,
            self._payload(),
            format="json",
        )

        project = Project.objects.get()

        self.assertTrue(
            ProjectMember.objects.filter(
                project=project,
                user=self.manager,
            ).exists()
        )

    def test_selected_members_are_added_to_project(self):
        self.client.post(
            self.url,
            self._payload(),
            format="json",
        )

        project = Project.objects.get()

        self.assertTrue(
            ProjectMember.objects.filter(
                project=project,
                user=self.employee,
            ).exists()
        )

    def test_creator_is_not_added_twice_if_in_member_ids(self):
        response = self.client.post(
            self.url,
            self._payload(
                member_ids=[
                    self.manager.pk,
                    self.employee.pk,
                ]
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        project = Project.objects.get()

        self.assertEqual(
            ProjectMember.objects.filter(
                project=project,
                user=self.manager,
            ).count(),
            1,
        )

    # -------------------------------------------------- API 04 validation

    def test_create_rejects_blank_project_name(self):
        response = self.client.post(
            self.url,
            self._payload(project_name="   "),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("project_name", response.data)

    def test_create_rejects_end_date_before_start_date(self):
        response = self.client.post(
            self.url,
            self._payload(
                start_date="2026-12-01",
                end_date="2026-10-01",
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("end_date", response.data)

    def test_create_rejects_member_from_another_organisation(self):
        response = self.client.post(
            self.url,
            self._payload(
                member_ids=[self.other_manager.pk]
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("member_ids", response.data)
        self.assertEqual(Project.objects.count(), 0)

    # ------------------------------------------------------- API 05 list

    def test_admin_can_see_all_projects_in_own_organisation(self):
        first = self._project(self.manager, "Project One")
        second = self._project(self.admin, "Project Two")

        self._project(
            self.other_manager,
            "Other Organisation Project",
        )

        self.client.force_authenticate(user=self.admin)

        response = self.client.get(self.url)

        ids = {
            row["project_id"]
            for row in response.data
        }

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            ids,
            {first.pk, second.pk},
        )

    def test_manager_can_see_project_they_created(self):
        project = self._project(
            self.manager,
            "Created By Manager",
        )

        response = self.client.get(self.url)

        ids = [
            row["project_id"]
            for row in response.data
        ]

        self.assertIn(project.pk, ids)

    def test_manager_can_see_project_they_belong_to(self):
        project = self._project(
            self.admin,
            "Manager Is Member",
        )

        ProjectMember.objects.create(
            project=project,
            user=self.manager,
        )

        response = self.client.get(self.url)

        ids = [
            row["project_id"]
            for row in response.data
        ]

        self.assertIn(project.pk, ids)

    def test_manager_cannot_see_unrelated_project(self):
        self._project(
            self.admin,
            "Manager Cannot See This",
        )

        response = self.client.get(self.url)

        self.assertEqual(
            list(response.data),
            [],
        )

    def test_employee_can_see_project_they_belong_to(self):
        project = self._project(
            self.manager,
            "Employee Project",
        )

        ProjectMember.objects.create(
            project=project,
            user=self.employee,
        )

        self.client.force_authenticate(user=self.employee)

        response = self.client.get(self.url)

        ids = [
            row["project_id"]
            for row in response.data
        ]

        self.assertIn(project.pk, ids)

    def test_employee_cannot_see_project_they_do_not_belong_to(self):
        self._project(
            self.manager,
            "Not Employee Project",
        )

        self.client.force_authenticate(user=self.employee)

        response = self.client.get(self.url)

        self.assertEqual(
            list(response.data),
            [],
        )

    def test_projects_from_other_organisation_are_not_visible(self):
        other_project = self._project(
            self.other_manager,
            "Private Other Project",
        )

        ProjectMember.objects.create(
            project=other_project,
            user=self.other_manager,
        )

        response = self.client.get(self.url)

        ids = [
            row["project_id"]
            for row in response.data
        ]

        self.assertNotIn(other_project.pk, ids)

    def test_empty_project_list_returns_empty_200(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            list(response.data),
            [],
        )

    # ------------------------------------------ authentication and routing

    def test_both_services_refuse_unauthenticated_user(self):
        self.client.force_authenticate(user=None)

        get_response = self.client.get(self.url)
        post_response = self.client.post(
            self.url,
            self._payload(),
            format="json",
        )

        self.assertIn(
            get_response.status_code,
            (
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ),
        )

        self.assertIn(
            post_response.status_code,
            (
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ),
        )

    def test_route_has_no_trailing_slash(self):
        self.assertFalse(self.url.endswith("/"))

        response = self.client.get(self.url + "/")

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )