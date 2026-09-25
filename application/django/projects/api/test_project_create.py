"""Tests for API 04 - POST /api/projects

Test owner: Edward
Implementation owner: Jessie

These are integration tests. Nothing is mocked and nothing is patched: every
case below goes through the real view, the real service, the real data-access
function and the real sp_create_project inside a local MySQL database. That is
what the section 19 line "SP integration tests run on the local test DB; no
test points at RDS" asks for, and it is the only kind of test that can catch a
procedure whose parameter order, column list or constraint is wrong.

Running them
------------
    cd application/django
    python manage.py test projects

DB_ENGINE must be mysql. There is no SQLite fallback, because SQLite cannot
execute a stored procedure. `manage.py test` creates and drops test_<DB_NAME>,
so confirm DB_HOST is 127.0.0.1 before running: pointed at RDS this would
create and drop a database on the shared server.

Why TransactionTestCase and not TestCase
----------------------------------------
sp_create_project manages its own transaction: it issues START TRANSACTION,
COMMIT and, in its exit handler, ROLLBACK. In MySQL a START TRANSACTION inside
a procedure implicitly commits whatever transaction was already open, which
would be the class-level transaction that TestCase relies on to undo a test.
TransactionTestCase does not depend on that transaction; it truncates the
tables between tests instead. It is slower, and it is correct here.

Why the organisation is called JNS Business Solutions
-----------------------------------------------------
sp_get_session_user resolves a session only for an active user in an active
organisation whose name is exactly 'JNS Business Solutions'. A caller placed
anywhere else has no session at all, so the fixture puts the whole cast in
that organisation and uses project membership, not a second organisation, to
express the negative cases.
"""

from django.test import TransactionTestCase

from data_access.sp_loader import load_stored_procedures
from projects.models import Project, ProjectMember
from users.models import Organisation, Role, User

URL = "/api/projects"


class ProjectCreateApiTests(TransactionTestCase):
    """API 04."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_stored_procedures(
            "users/sp_get_session_user",
            "projects/sp_create_project",
            "projects/sp_get_projects",
        )

    def setUp(self):
        self.admin_role = Role.objects.create(role_name="Admin")
        self.manager_role = Role.objects.create(role_name="Manager")
        self.employee_role = Role.objects.create(role_name="Employee")

        self.org = self._organisation("JNS Business Solutions")

        self.admin = self._user(self.org, "boss@jns.test", self.admin_role)
        self.manager = self._user(self.org, "edward@jns.test", self.manager_role)
        self.employee = self._user(self.org, "worker@jns.test", self.employee_role)
        self.colleague = self._user(self.org, "other@jns.test", self.employee_role)

        # Active user in a different organisation. Never a valid member, and
        # never a valid caller either, because the session procedure will not
        # resolve anyone outside JNS Business Solutions.
        self.other_org = self._organisation("Unrelated Charity")
        self.outsider = self._user(
            self.other_org, "someone@charity.test", self.manager_role
        )

        # Same organisation, but suspended. sp_create_project must refuse to
        # add this user as a member.
        self.suspended = self._user(
            self.org, "gone@jns.test", self.employee_role, status="Suspended"
        )

    # ----------------------------------------------------------- helpers

    def _organisation(self, name):
        return Organisation.objects.create(
            organisation_name=name,
            organisation_type="SME",
            email=f"info@{name.split()[0].lower()}.test",
            phone="09-000-0000",
            address="1 Test Street",
            status="Active",
        )

    def _user(self, org, email, role, status="Active"):
        return User.objects.create_user(
            email=email,
            organisation=org,
            role=role,
            password="Passw0rd!",
            first_name=email.split("@")[0].title(),
            last_name="Test",
            status=status,
        )

    def _login_as(self, user):
        session = self.client.session
        session["user_id"] = user.user_id
        session.save()

    def _body(self, **overrides):
        body = {
            "project_name": "Annual Accounts 2026",
            "description": "End of year accounts for the SME portfolio.",
            "start_date": "2026-10-01",
            "end_date": "2026-12-20",
            "member_ids": [],
        }
        body.update(overrides)

        return body

    def _post(self, body):
        return self.client.post(URL, data=body, content_type="application/json")

    # ------------------------------------------ authentication and role

    def test_no_session_returns_401_and_writes_nothing(self):
        response = self._post(self._body())

        self.assertEqual(response.status_code, 401)
        self.assertEqual(Project.objects.count(), 0)

    def test_session_pointing_at_a_deleted_user_returns_401(self):
        self._login_as(self.manager)
        user_id = self.manager.user_id
        self.manager.delete()

        response = self._post(self._body())

        self.assertEqual(response.status_code, 401)
        self.assertFalse(User.objects.filter(user_id=user_id).exists())

    def test_employee_returns_403_and_writes_nothing(self):
        self._login_as(self.employee)

        response = self._post(self._body())

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Project.objects.count(), 0)

    def test_manager_may_create(self):
        self._login_as(self.manager)

        self.assertEqual(self._post(self._body()).status_code, 201)

    def test_admin_may_create(self):
        self._login_as(self.admin)

        self.assertEqual(self._post(self._body()).status_code, 201)

    # -------------------------------------------------------- happy path

    def test_create_returns_201_and_the_row_the_procedure_wrote(self):
        self._login_as(self.manager)

        response = self._post(self._body())
        payload = response.json()["project"]

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Project.objects.count(), 1)

        project = Project.objects.get()

        self.assertEqual(payload["project_id"], project.project_id)
        self.assertEqual(payload["project_name"], "Annual Accounts 2026")
        self.assertEqual(
            payload["description"],
            "End of year accounts for the SME portfolio.",
        )
        self.assertEqual(str(payload["start_date"]), "2026-10-01")
        self.assertEqual(str(payload["end_date"]), "2026-12-20")

    def test_the_procedure_derives_the_fields_the_body_never_sent(self):
        """status, created_at and updated_at are set by sp_create_project."""

        self._login_as(self.manager)

        payload = self._post(self._body()).json()["project"]

        self.assertEqual(payload["status"], "Active")
        self.assertIsNotNone(payload["created_at"])
        self.assertIsNotNone(payload["updated_at"])

    def test_organisation_and_author_come_from_the_session_not_the_body(self):
        self._login_as(self.manager)

        response = self._post(
            self._body(
                organisation_id=self.other_org.organisation_id,
                created_by=self.outsider.user_id,
                status="Archived",
            )
        )

        project = Project.objects.get()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(project.organisation_id, self.org.organisation_id)
        self.assertEqual(project.created_by_id, self.manager.user_id)
        self.assertEqual(project.status, "Active")

    def test_description_and_dates_are_optional(self):
        self._login_as(self.manager)

        response = self._post({"project_name": "Bare minimum project"})
        project = Project.objects.get()

        self.assertEqual(response.status_code, 201)
        self.assertIsNone(project.description)
        self.assertIsNone(project.start_date)
        self.assertIsNone(project.end_date)

    def test_the_title_is_stored_without_its_surrounding_whitespace(self):
        self._login_as(self.manager)

        self._post(self._body(project_name="   Padded name   "))

        self.assertEqual(Project.objects.get().project_name, "Padded name")

    # ------------------------------------------------------------ members

    def test_members_are_written_in_the_same_call(self):
        self._login_as(self.manager)

        response = self._post(
            self._body(
                member_ids=[self.employee.user_id, self.colleague.user_id]
            )
        )

        project = Project.objects.get()
        member_ids = set(
            ProjectMember.objects.filter(project=project).values_list(
                "user_id", flat=True
            )
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            member_ids, {self.employee.user_id, self.colleague.user_id}
        )

    def test_a_member_from_another_organisation_is_refused(self):
        self._login_as(self.manager)

        response = self._post(self._body(member_ids=[self.outsider.user_id]))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Project.objects.count(), 0)
        self.assertEqual(ProjectMember.objects.count(), 0)

    def test_a_suspended_member_is_refused(self):
        self._login_as(self.manager)

        response = self._post(self._body(member_ids=[self.suspended.user_id]))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Project.objects.count(), 0)

    def test_a_member_id_that_does_not_exist_is_refused(self):
        self._login_as(self.manager)

        response = self._post(self._body(member_ids=[999999]))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Project.objects.count(), 0)

    def test_one_bad_member_rolls_back_the_whole_project(self):
        """The project and the good member must not survive the failure."""

        self._login_as(self.manager)

        response = self._post(
            self._body(
                member_ids=[self.employee.user_id, self.outsider.user_id]
            )
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Project.objects.count(), 0)
        self.assertEqual(ProjectMember.objects.count(), 0)

    def test_the_same_member_twice_is_refused(self):
        self._login_as(self.manager)

        response = self._post(
            self._body(
                member_ids=[self.employee.user_id, self.employee.user_id]
            )
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Project.objects.count(), 0)

    # --------------------------------------------------------- validation

    def test_a_missing_name_is_refused(self):
        self._login_as(self.manager)

        response = self._post({"description": "No name at all."})

        self.assertEqual(response.status_code, 400)
        self.assertIn("project_name", response.json())
        self.assertEqual(Project.objects.count(), 0)

    def test_a_blank_name_is_refused(self):
        self._login_as(self.manager)

        response = self._post(self._body(project_name="   "))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Project.objects.count(), 0)

    def test_a_name_over_150_characters_is_refused(self):
        self._login_as(self.manager)

        response = self._post(self._body(project_name="x" * 151))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Project.objects.count(), 0)

    def test_a_name_of_exactly_150_characters_is_accepted(self):
        self._login_as(self.manager)

        response = self._post(self._body(project_name="x" * 150))

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(Project.objects.get().project_name), 150)

    def test_an_end_date_before_the_start_date_is_refused(self):
        self._login_as(self.manager)

        response = self._post(
            self._body(start_date="2026-12-20", end_date="2026-10-01")
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Project.objects.count(), 0)

    def test_the_same_start_and_end_date_is_accepted(self):
        self._login_as(self.manager)

        response = self._post(
            self._body(start_date="2026-10-01", end_date="2026-10-01")
        )

        self.assertEqual(response.status_code, 201)

    def test_a_malformed_date_is_refused(self):
        self._login_as(self.manager)

        response = self._post(self._body(start_date="20th of October"))

        self.assertEqual(response.status_code, 400)
        self.assertIn("start_date", response.json())

    def test_a_non_integer_member_id_is_refused(self):
        self._login_as(self.manager)

        response = self._post(self._body(member_ids=["not-a-number"]))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Project.objects.count(), 0)

    # ------------------------------------------------------- round trip

    def test_the_created_project_is_readable_through_the_list_procedure(self):
        """The read goes through sp_get_projects, so both procedures agree."""

        self._login_as(self.manager)

        created = self._post(self._body()).json()["project"]

        listed = self.client.get(URL).json()["projects"]
        match = [
            row for row in listed if row["project_id"] == created["project_id"]
        ]

        self.assertEqual(len(match), 1)
        self.assertEqual(match[0]["project_name"], created["project_name"])
        self.assertEqual(match[0]["status"], "Active")
        self.assertEqual(
            match[0]["organisation_id"], self.org.organisation_id
        )
