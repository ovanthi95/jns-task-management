"""Tests for API 06 - POST /api/projects/:projectId/tasks

Test owner: Edward

The cast, the payload helper and the stored-procedure loading all come from
ProjectTaskFixture in tasks/tests.py, so API 06 and API 07 are tested against
the same world rather than two that could drift apart. That module's docstring
explains how to run these and why they need MySQL.

Assertions here are about status codes and which field carries the error, not
about the wording of a message. The wording is allowed to improve without a
test having to be rewritten; what a caller can act on is the status and the
field name.
"""

from rest_framework import status

from projects.models import Project

from ..models import Task, TaskAssignee
from ..tests import ProjectTaskFixture


class TaskCreateTests(ProjectTaskFixture):
    """API 06."""

    # ------------------------------------------------------- happy path

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
        self.assertIsNone(response.data["description"])

    def test_the_stored_timestamps_are_set_by_the_procedure(self):
        """A raw INSERT skips Django's auto_now_add, so both are asserted.

        Left to the column defaults, updated_at would be NULL and the read
        contract would publish a null for a field it says is always present.
        """

        response = self.client.post(self.url, self._payload(), format="json")

        self.assertIsNotNone(response.data["created_at"])
        self.assertIsNotNone(response.data["updated_at"])

    # ------------------------------------------------------- validation

    def test_create_rejects_a_missing_lookup(self):
        response = self.client.post(
            self.url,
            {"title": "No lookups supplied"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        for field in ("task_type_id", "status_id", "priority_id", "assignee_id"):
            self.assertIn(field, response.data)

    def test_create_rejects_a_lookup_id_that_does_not_exist(self):
        """400 with the field named, not a 500 from the foreign key.

        This is the check that would be missing if the create path resolved
        the lookups by letting the INSERT fail.
        """

        response = self.client.post(
            self.url,
            self._payload(task_type_id=999999),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("task_type_id", response.data)
        self.assertEqual(Task.objects.count(), 0)

    def test_create_reports_every_bad_lookup_at_once(self):
        """Three bad ids are three errors in one response, not three requests."""

        response = self.client.post(
            self.url,
            self._payload(
                task_type_id=999999,
                status_id=999998,
                priority_id=999997,
            ),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        for field in ("task_type_id", "status_id", "priority_id"):
            self.assertIn(field, response.data)

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

    # ------------------------------------------------------- assignment

    def test_create_also_writes_the_assignment_row(self):
        """"Create and assign" means both rows, not just the task."""

        self.client.post(self.url, self._payload(), format="json")

        task = Task.objects.get()
        assignment = TaskAssignee.objects.get()

        self.assertEqual(assignment.task_id, task.pk)
        self.assertEqual(assignment.user_id, self.assignee.pk)
        self.assertEqual(assignment.assigned_by_id, self.user.pk)
        self.assertIsNone(assignment.assignment_role)

    def test_the_201_response_includes_the_assignee(self):
        """The caller should not have to call API 07 to see what it just did."""

        response = self.client.post(self.url, self._payload(), format="json")

        self.assertEqual(
            response.data["assignees"],
            [
                {
                    "user_id": self.assignee.pk,
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "assignment_role": None,
                }
            ],
        )

    def test_the_assignee_shape_carries_no_account_fields(self):
        """Names and ids only. The procedure selects four columns from a join
        against users, so the absence of the rest is asserted rather than
        assumed."""

        response = self.client.post(self.url, self._payload(), format="json")

        assignee = response.data["assignees"][0]

        for leaked in ("email", "password", "password_hash", "role", "status"):
            self.assertNotIn(leaked, assignee)

    def test_create_rejects_a_missing_assignee(self):
        payload = self._payload()
        payload.pop("assignee_id")

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("assignee_id", response.data)

    def test_create_rejects_an_assignee_who_does_not_exist(self):
        response = self.client.post(
            self.url,
            self._payload(assignee_id=999999),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("assignee_id", response.data)

    def test_create_rejects_an_assignee_from_another_organisation(self):
        response = self.client.post(
            self.url,
            self._payload(assignee_id=self.other_user.pk),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("assignee_id", response.data)

    def test_create_rejects_an_assignee_who_is_not_a_project_member(self):
        """Same organisation is not enough; the assignee must be on the project."""

        response = self.client.post(
            self.url,
            self._payload(assignee_id=self.outsider.pk),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("assignee_id", response.data)

    def test_a_rejected_assignee_leaves_no_task_behind(self):
        """The task and the assignment are written together or not at all."""

        self.client.post(
            self.url,
            self._payload(assignee_id=self.outsider.pk),
            format="json",
        )

        self.assertEqual(Task.objects.count(), 0)
        self.assertEqual(TaskAssignee.objects.count(), 0)

    # --------------------------------------------------- role restriction

    def test_a_manager_can_create_a_task(self):
        response = self.client.post(self.url, self._payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_an_admin_can_create_a_task(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(self.url, self._payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_an_employee_cannot_create_a_task(self):
        """403 rather than 404: this is about the caller, not the project."""

        self.client.force_authenticate(user=self.assignee)

        response = self.client.post(self.url, self._payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Task.objects.count(), 0)

    def test_the_role_is_answered_before_the_body(self):
        """A forbidden role is told so, not told its body was malformed.

        The role belongs to the caller; the body's problems would be a hint
        about a service this caller cannot use either way.
        """

        self.client.force_authenticate(user=self.assignee)

        response = self.client.post(self.url, {"title": ""}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --------------------------------------------------------- tenancy

    def test_same_organisation_non_member_cannot_create_a_task(self):
        self.client.force_authenticate(user=self.outsider)

        response = self.client.post(self.url, self._payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Task.objects.count(), 0)

    def test_another_organisation_cannot_create_a_task_here(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(self.url, self._payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Task.objects.count(), 0)

    def test_an_unknown_project_cannot_be_written_to(self):
        response = self.client.post(
            "/api/projects/999999/tasks",
            self._payload(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Task.objects.count(), 0)

    def test_a_project_in_another_organisation_is_404_not_403(self):
        """The caller's role is fine, so only the project can be the reason."""

        other_project = Project.objects.create(
            organisation=self.other_org,
            project_name="Someone Else's Work",
            created_by=self.other_user,
        )

        response = self.client.post(
            f"/api/projects/{other_project.pk}/tasks",
            self._payload(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --------------------------------------------------------- routing

    def test_the_route_has_no_trailing_slash(self):
        """A trailing slash is a clean 404, not a redirect that drops the body.

        APPEND_SLASH only redirects when the slashed form matches a route.
        Here the unslashed form is the one registered, so nothing redirects
        and a POST body can never be silently lost.
        """

        self.assertFalse(self.url.endswith("/"))

        response = self.client.post(self.url + "/", self._payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
