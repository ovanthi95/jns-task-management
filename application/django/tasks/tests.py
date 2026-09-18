"""Tests for API 06 and API 07.

    API 06  POST /api/projects/:projectId/tasks
    API 07  GET  /api/projects/:projectId/tasks

Run them against SQLite, never against RDS:

    cd application/django
    DB_ENGINE=sqlite python manage.py test tasks

The exported variable matters. `manage.py test` creates and then drops a
database called test_<name>, so if DB_ENGINE is mysql it will do that on
whatever DB_HOST points at. load_dotenv() does not override variables that are
already in the environment, so setting it on the command line wins over .env.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from projects.models import Project
from users.models import Organisation, Role, User

from .models import Priority, Task, TaskStatus, TaskType


class ProjectTaskApiTests(TestCase):
    """Two organisations, so tenant isolation is testable rather than assumed."""

    def setUp(self):
        self.role = Role.objects.create(role_name="Manager")

        self.org = self._organisation("JNS Business Solutions")
        self.other_org = self._organisation("Unrelated Charity")

        self.user = self._user(self.org, "edward@jns.test")
        self.other_user = self._user(self.other_org, "someone@charity.test")

        self.project = Project.objects.create(
            organisation=self.org,
            project_name="Annual Accounts 2026",
            created_by=self.user,
        )

        self.task_type = TaskType.objects.create(
            type_name="Accounting",
            display_order=1,
        )
        self.task_status = TaskStatus.objects.create(
            status_name="New",
            display_order=1,
        )
        self.priority = Priority.objects.create(
            priority_name="High",
            priority_level=1,
        )

        self.url = reverse("project-tasks", args=[self.project.pk])

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

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

    def _user(self, organisation, email):
        return User.objects.create_user(
            email=email,
            organisation=organisation,
            role=self.role,
            password="not-a-real-password",
            first_name="Test",
            last_name="User",
        )

    def _payload(self, **overrides):
        """The body the React form sends, with per-test overrides."""

        payload = {
            "task_type_id": self.task_type.pk,
            "status_id": self.task_status.pk,
            "priority_id": self.priority.pk,
            "title": "File the GST return",
            "description": "Quarter three.",
            "start_date": "2026-10-01",
            "due_date": "2026-10-20",
            "estimated_hours": "4.50",
        }

        payload.update(overrides)

        return payload

    # ------------------------------------------------- API 06, happy path

    def test_create_returns_201_and_the_new_task(self):
        response = self.client.post(self.url, self._payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "File the GST return")
        self.assertEqual(response.data["project_id"], self.project.pk)
        self.assertEqual(response.data["status_name"], "New")
        self.assertEqual(Task.objects.count(), 1)

    def test_create_takes_project_from_the_url_and_author_from_the_user(self):
        self.client.post(self.url, self._payload(), format="json")

        task = Task.objects.get()

        self.assertEqual(task.project_id, self.project.pk)
        self.assertEqual(task.created_by_id, self.user.pk)

    def test_create_ignores_a_forged_author_or_organisation(self):
        """The body must not be able to reassign ownership."""

        payload = self._payload(
            created_by=self.other_user.pk,
            project=999,
            organisation_id=self.other_org.pk,
        )

        response = self.client.post(self.url, payload, format="json")
        task = Task.objects.get()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(task.created_by_id, self.user.pk)
        self.assertEqual(task.project_id, self.project.pk)

    def test_create_strips_surrounding_whitespace_from_the_title(self):
        response = self.client.post(
            self.url,
            self._payload(title="   Padded title   "),
            format="json",
        )

        self.assertEqual(response.data["title"], "Padded title")

    def test_create_accepts_a_null_description(self):
        response = self.client.post(
            self.url,
            self._payload(description=None),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # ------------------------------------------------- API 06, validation

    def test_create_rejects_a_missing_lookup(self):
        response = self.client.post(
            self.url,
            {"title": "No lookups supplied"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        for field in ("task_type_id", "status_id", "priority_id"):
            self.assertIn(field, response.data)

    def test_create_rejects_a_lookup_id_that_does_not_exist(self):
        response = self.client.post(
            self.url,
            self._payload(task_type_id=999999),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("task_type_id", response.data)

    def test_create_rejects_a_blank_title(self):
        response = self.client.post(
            self.url,
            self._payload(title="   "),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)

    def test_create_rejects_a_title_over_200_characters(self):
        response = self.client.post(
            self.url,
            self._payload(title="x" * 201),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)

    def test_create_rejects_a_due_date_before_the_start_date(self):
        response = self.client.post(
            self.url,
            self._payload(start_date="2026-10-20", due_date="2026-10-01"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("due_date", response.data)

    def test_create_rejects_non_numeric_estimated_hours(self):
        response = self.client.post(
            self.url,
            self._payload(estimated_hours="four"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("estimated_hours", response.data)

    # --------------------------------------------------------- API 07

    def test_list_returns_only_the_tasks_of_the_project_in_the_url(self):
        other_project = Project.objects.create(
            organisation=self.org,
            project_name="Payroll Migration",
            created_by=self.user,
        )

        self.client.post(self.url, self._payload(title="Belongs here"), format="json")
        self.client.post(
            reverse("project-tasks", args=[other_project.pk]),
            self._payload(title="Belongs elsewhere"),
            format="json",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([t["title"] for t in response.data], ["Belongs here"])

    def test_list_includes_the_lookup_names_not_just_the_ids(self):
        self.client.post(self.url, self._payload(), format="json")

        row = self.client.get(self.url).data[0]

        self.assertEqual(row["task_type_name"], "Accounting")
        self.assertEqual(row["status_name"], "New")
        self.assertEqual(row["priority_name"], "High")

    # ------------------------------------------- tenancy and authentication

    def test_another_organisation_cannot_list_this_projects_tasks(self):
        """404 rather than 403, so the project's existence is not confirmed."""

        self.client.force_authenticate(user=self.other_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_another_organisation_cannot_create_a_task_here(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(self.url, self._payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Task.objects.count(), 0)

    def test_an_unknown_project_is_404(self):
        response = self.client.get(reverse("project-tasks", args=[999999]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_both_services_refuse_an_unauthenticated_caller(self):
        self.client.force_authenticate(user=None)

        self.assertIn(
            self.client.get(self.url).status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )
        self.assertIn(
            self.client.post(self.url, self._payload(), format="json").status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    # ------------------------------------------------------------- routing

    def test_the_route_has_no_trailing_slash(self):
        """A trailing slash is a clean 404, not a redirect that drops the body.

        APPEND_SLASH only redirects when the slashed form matches a route.
        Here the unslashed form is the one registered, so nothing redirects
        and a POST body can never be silently lost.
        """

        self.assertFalse(self.url.endswith("/"))

        response = self.client.post(self.url + "/", self._payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
