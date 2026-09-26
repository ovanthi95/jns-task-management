"""API 07 tests, plus the fixture both task test files share.

    API 07  GET /api/projects/:projectId/tasks

API 06's tests live in tasks/api/test_task_create.py, which is the file the
playbook's map gives to this endpoint's test owner. API 07's test file,
tasks/api/test_task_list.py, belongs to Jesse, so the API 07 tests stay here
rather than being written into someone else's file. They move when he picks it
up; ProjectTaskFixture is importable from there as it is from here.

Running them
------------
These are MySQL integration tests and there is no SQLite fallback, because the
endpoints call stored procedures and SQLite cannot execute them.

    cd application/django
    python manage.py test tasks

DB_ENGINE must be mysql, which is what .env already sets. `manage.py test`
creates and drops a database called test_<DB_NAME>, so check DB_HOST is
127.0.0.1 before running: pointed at RDS this would create and drop a database
on the shared server.

Loading the procedures
----------------------
The test database is built by migrate, which creates tables and nothing else,
so the procedures have to be loaded into it before any test runs. That is what
load_stored_procedures does, and it is called from setUpClass before the
class-level transaction opens: CREATE PROCEDURE causes an implicit commit in
MySQL, so running it inside a test would end the transaction that TestCase
relies on to roll the test back.

load_stored_procedures is Manatka's shared loader (data_access/sp_loader.py).
This module used to carry its own copy limited to the tasks/ folder; that copy
is gone, which is also what the endpoints now need, because the caller is read
through users/sp_get_session_user and the old loader could not reach outside
tasks/.

Signing a caller in
-------------------
These tests do not use force_authenticate. The task endpoints read the caller
out of request.session, the way APIs 01 to 05 and 10 do, so a test that
injected a user object would pass while a real browser session got a 401. The
fixture's _login_as writes the session cookie instead, which is the same thing
API 01 does on a successful login. tasks/api/_session.py has the reasoning.
"""

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from data_access.sp_loader import load_stored_procedures
from projects.models import Project, ProjectMember
from users.models import Organisation, Role, User

from .models import Priority, Task, TaskStatus, TaskType
from .services.exceptions import ProjectNotVisible
from .services.project_access import require_visible_project

# Only the procedures API 06 and API 07 call, plus the session lookup every
# request goes through. The tasks folder also holds stubs for cards that
# belong to other people, and loading those would make this suite fail for a
# reason that has nothing to do with these two endpoints.
PROCEDURE_NAMES = (
    "users/sp_get_session_user",
    "tasks/sp_create_task",
    "tasks/sp_get_project_tasks",
    "tasks/sp_get_project_user_access",
    "tasks/sp_check_task_lookups",
)


class ProjectTaskFixture(TestCase):
    """Two organisations, so tenant isolation is testable rather than assumed.

    The cast, and why each one exists:

        user       Manager, member of the project. The usual caller.
        assignee   Employee, member of the project. The usual assignee, and
                   the proof that the role rule applies to creating a task
                   rather than to being given one.
        admin      Admin, member. The other role allowed to create.
        outsider   Manager, same organisation, deliberately NOT a member.
        other_user Manager in a different organisation entirely.

    other_user cannot be signed in. sp_get_session_user only resolves a
    session for a user whose organisation is literally named "JNS Business
    Solutions", so a caller from another organisation gets a 401 before the
    project is ever looked at. The cross-organisation rule is therefore
    asserted the other way round - a JNS caller reaching for a project that
    belongs to other_org - and once directly against the service, rather than
    by pretending the procedure would hand out that session.

    Subclassed rather than mixed in, so a subclass inherits the procedure
    loading as well as the cast and cannot be written without it.
    """

    @classmethod
    def setUpClass(cls):
        # Before super(), which opens the class-level transaction. See the
        # module docstring.
        load_stored_procedures(*PROCEDURE_NAMES)
        super().setUpClass()

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
        self._login_as(self.user)

    # ----------------------------------------------------------- helpers

    def _login_as(self, user):
        """Give the client a session for `user`, the way API 01 would.

        API 01 stores nothing but the id: request.session["user_id"]. Every
        request then resolves that id through sp_get_session_user, so the row
        has to be Active and in an Active "JNS Business Solutions", or the
        endpoint answers 401 no matter what this helper writes.
        """

        session = self.client.session
        session["user_id"] = user.pk
        session.save()

        self.client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

    def _log_out(self):
        """Drop the session cookie, leaving an anonymous client."""

        self.client.cookies.pop(settings.SESSION_COOKIE_NAME, None)

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


class ProjectTaskListTests(ProjectTaskFixture):
    """API 07.

    Tasks are set up by posting to API 06 rather than by writing rows with the
    ORM, so what is listed is what the create service actually produced. A bug
    that made the two disagree would fail here rather than hide.
    """

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

    def test_list_keeps_the_decimal_and_datetime_wire_format(self):
        """The ORM is gone, so the contract's own formatting is asserted.

        estimated_hours has to stay a string with two decimal places, and the
        timestamps have to stay UTC with a trailing Z. A raw value straight
        from the driver would render the first as a float.
        """

        self.client.post(self.url, self._payload(), format="json")

        row = self.client.get(self.url).data[0]

        self.assertEqual(row["estimated_hours"], "4.50")
        self.assertIsNone(row["actual_hours"])
        self.assertEqual(row["start_date"], "2026-10-01")
        self.assertTrue(row["created_at"].endswith("Z"))

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

    def test_an_employee_can_still_list_tasks(self):
        """The role rule is scoped to creating, not to reading."""

        self.client.post(self.url, self._payload(), format="json")
        self._login_as(self.assignee)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

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

        self._login_as(self.outsider)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_a_project_in_another_organisation_is_404(self):
        """404 rather than 403, so the project's existence is not confirmed.

        Driven from the JNS side rather than from the other organisation's,
        because sp_get_session_user will not issue a session to a user outside
        JNS Business Solutions. See the fixture docstring.
        """

        other_project = Project.objects.create(
            organisation=self.other_org,
            project_name="Someone Else's Work",
            created_by=self.other_user,
        )
        self._member(other_project, self.other_user)

        response = self.client.get(
            reverse("project-tasks", args=[other_project.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_the_service_refuses_a_caller_from_another_organisation(self):
        """The same rule from the other direction, below the HTTP layer.

        require_visible_project is what both task services call, and it takes
        the session dict rather than a request, so it can be asked the
        question the endpoint cannot: what happens when the caller really is
        in another organisation. Kept as a service test rather than dropped,
        so tenant isolation is asserted somewhere rather than assumed.
        """

        with self.assertRaises(ProjectNotVisible):
            require_visible_project(
                project_id=self.project.pk,
                user={
                    "user_id": self.other_user.pk,
                    "organisation_id": self.other_org.pk,
                    "role_name": "Manager",
                },
            )

    def test_an_unknown_project_is_404(self):
        response = self.client.get(reverse("project-tasks", args=[999999]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_both_services_refuse_an_unauthenticated_caller(self):
        self._log_out()

        self.assertEqual(
            self.client.get(self.url).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(
            self.client.post(self.url, self._payload(), format="json").status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(Task.objects.count(), 0)

    def test_a_session_for_a_user_who_no_longer_resolves_is_401(self):
        """A stale cookie is not a session.

        The id in the cookie is looked up on every request, so a user who has
        since been suspended is refused even though the cookie is still valid
        and signed.
        """

        self.user.status = "Suspended"
        self.user.save(update_fields=["status"])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
