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

from projects.models import Project, ProjectMember
from users.models import Organisation, Role, User

from .models import Priority, Task, TaskAssignee, TaskStatus, TaskType


class ProjectTaskApiTests(TestCase):
    """Two organisations, so tenant isolation is testable rather than assumed.

    The cast, and why each one exists:

        user       Manager, member of the project. The usual caller.
        assignee   Employee, member of the project. The usual assignee, and
                   the proof that the role rule applies to creating a task
                   rather than to being given one.
        admin      Admin, member. The other role allowed to create.
        outsider   Manager, same organisation, deliberately NOT a member.
        other_user Manager in a different organisation entirely.
    """

    def setUp(self):
        self.manager_role = Role.objects.create(role_name="Manager")
        self.admin_role = Role.objects.create(role_name="Admin")
        self.employee_role = Role.objects.create(role_name="Employee")

        self.org = self._organisation("JNS Business Solutions")
        self.other_org = self._organisation("Unrelated Charity")

        self.user = self._user(self.org, "edward@jns.test", self.manager_role)
        # Named, unlike the rest of the cast, so the assignee in a response
        # body can be told apart from whoever made the request.
        self.assignee = self._user(
            self.org,
            "worker@jns.test",
            self.employee_role,
            first_name="Jane",
            last_name="Smith",
        )
        self.admin = self._user(self.org, "boss@jns.test", self.admin_role)
        self.outsider = self._user(self.org, "nobody@jns.test", self.manager_role)

        self.other_user = self._user(
            self.other_org,
            "someone@charity.test",
            self.manager_role,
        )

        self.project = Project.objects.create(
            organisation=self.org,
            project_name="Annual Accounts 2026",
            created_by=self.user,
        )

        # Membership is explicit, including for the user who created the
        # project. API 06/07 do not infer it from Project.created_by.
        self._member(self.project, self.user)
        self._member(self.project, self.assignee)
        self._member(self.project, self.admin)

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

    def _user(
        self,
        organisation,
        email,
        role,
        first_name="Test",
        last_name="User",
    ):
        return User.objects.create_user(
            email=email,
            organisation=organisation,
            role=role,
            password="not-a-real-password",
            first_name=first_name,
            last_name=last_name,
        )

    def _member(self, project, user):
        return ProjectMember.objects.create(project=project, user=user)

    def _payload(self, **overrides):
        """A valid API 06 body, with per-test overrides."""

        payload = {
            "task_type_id": self.task_type.pk,
            "status_id": self.task_status.pk,
            "priority_id": self.priority.pk,
            "assignee_id": self.assignee.pk,
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

        for field in ("task_type_id", "status_id", "priority_id", "assignee_id"):
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

    # ------------------------------------------------- API 06, assignment

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
        """Names and ids only. The email and password hash are one foreign key
        away from this serializer, so the absence is asserted rather than
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

    # ----------------------------------------------- API 06, role restriction

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

    def test_an_employee_can_still_list_tasks(self):
        """The role rule is scoped to creating, not to reading."""

        self.client.post(self.url, self._payload(), format="json")
        self.client.force_authenticate(user=self.assignee)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    # --------------------------------------------------------- API 07

    def test_list_returns_only_the_tasks_of_the_project_in_the_url(self):
        other_project = Project.objects.create(
            organisation=self.org,
            project_name="Payroll Migration",
            created_by=self.user,
        )

        # Both users need membership of the second project too, or the second
        # POST would 404 and this test would pass for the wrong reason.
        self._member(other_project, self.user)
        self._member(other_project, self.assignee)

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

    def test_list_rows_include_the_assignees(self):
        """Same array as API 06 returns, so one read shape covers both."""

        self.client.post(self.url, self._payload(), format="json")

        row = self.client.get(self.url).data[0]

        self.assertEqual(
            row["assignees"],
            [
                {
                    "user_id": self.assignee.pk,
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "assignment_role": None,
                }
            ],
        )

    def test_list_of_a_project_with_no_tasks_is_an_empty_200(self):
        """An empty project is a success with nothing in it, not a 404."""

        empty_project = Project.objects.create(
            organisation=self.org,
            project_name="Not Started Yet",
            created_by=self.user,
        )
        self._member(empty_project, self.user)

        response = self.client.get(
            reverse("project-tasks", args=[empty_project.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(list(response.data), [])

    def test_list_is_ordered_newest_first(self):
        for title in ("First", "Second", "Third"):
            self.client.post(self.url, self._payload(title=title), format="json")

        response = self.client.get(self.url)

        self.assertEqual(
            [row["title"] for row in response.data],
            ["Third", "Second", "First"],
        )

    # --------------------------------------------------- API 07, filtering

    def test_list_filters_by_status_id(self):
        done = TaskStatus.objects.create(status_name="Completed", display_order=2)

        self.client.post(self.url, self._payload(title="Still open"), format="json")
        self.client.post(
            self.url,
            self._payload(title="Finished", status_id=done.pk),
            format="json",
        )

        response = self.client.get(self.url, {"status_id": done.pk})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row["title"] for row in response.data], ["Finished"])

    def test_list_filters_by_priority_id(self):
        low = Priority.objects.create(priority_name="Low", priority_level=1)

        self.client.post(self.url, self._payload(title="Urgent one"), format="json")
        self.client.post(
            self.url,
            self._payload(title="Relaxed one", priority_id=low.pk),
            format="json",
        )

        response = self.client.get(self.url, {"priority_id": low.pk})

        self.assertEqual([row["title"] for row in response.data], ["Relaxed one"])

    def test_list_filters_by_assignee_id(self):
        """Filtering joins through task_assignees and returns each task once."""

        self.client.post(self.url, self._payload(title="For the worker"), format="json")
        self.client.post(
            self.url,
            self._payload(title="For the admin", assignee_id=self.admin.pk),
            format="json",
        )

        response = self.client.get(self.url, {"assignee_id": self.admin.pk})

        self.assertEqual([row["title"] for row in response.data], ["For the admin"])

    def test_list_combines_filters_with_and(self):
        done = TaskStatus.objects.create(status_name="Completed", display_order=2)

        self.client.post(
            self.url,
            self._payload(title="Done by the worker", status_id=done.pk),
            format="json",
        )
        self.client.post(
            self.url,
            self._payload(title="Open for the admin", assignee_id=self.admin.pk),
            format="json",
        )
        self.client.post(
            self.url,
            self._payload(
                title="Done by the admin",
                status_id=done.pk,
                assignee_id=self.admin.pk,
            ),
            format="json",
        )

        response = self.client.get(
            self.url,
            {"status_id": done.pk, "assignee_id": self.admin.pk},
        )

        self.assertEqual(
            [row["title"] for row in response.data],
            ["Done by the admin"],
        )

    def test_list_rejects_a_filter_that_is_not_a_number(self):
        """A malformed query parameter is a bad request, not a server error.

        Checked on all three filters, because the rule is meant to be the
        same for each one.
        """

        for name in ("status_id", "priority_id", "assignee_id"):
            with self.subTest(filter=name):
                response = self.client.get(self.url, {name: "abc"})

                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )
                self.assertIn(name, response.data)

    def test_list_filter_id_that_matches_nothing_is_an_empty_200(self):
        """A valid integer that selects no rows is not an error."""

        self.client.post(self.url, self._payload(), format="json")

        for name in ("status_id", "priority_id", "assignee_id"):
            with self.subTest(filter=name):
                response = self.client.get(self.url, {name: 999999})

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(list(response.data), [])

    def test_list_ignores_a_query_parameter_outside_the_contract(self):
        """Only the three agreed filters exist; anything else changes nothing."""

        self.client.post(self.url, self._payload(), format="json")

        response = self.client.get(self.url, {"q": "anything"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    # ------------------------------------------- tenancy and authentication

    def test_same_organisation_non_member_cannot_list_the_tasks(self):
        """Being in the organisation is not enough. Membership is explicit."""

        self.client.force_authenticate(user=self.outsider)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_same_organisation_non_member_cannot_create_a_task(self):
        self.client.force_authenticate(user=self.outsider)

        response = self.client.post(self.url, self._payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Task.objects.count(), 0)

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
