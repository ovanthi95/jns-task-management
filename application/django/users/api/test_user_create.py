"""Tests for API 03 - POST /api/users

Test owner: Edward
Implementation owner: Manatka

Baseline cases from the implementation owner: 401, 403, 201 with safe
fields, password hashed in DB, duplicate email 400, unknown role 400,
missing fields 400, organisation taken from session not body.
Edward may add or adjust cases here.

MySQL only; procedures are loaded before the class-level transaction.
"""

from django.test import TestCase
from rest_framework import status

from audit.models import AuditLog
from data_access.sp_loader import load_stored_procedures
from users.models import Organisation, Role, User

URL = "/api/users"

VALID_BODY = {
    "first_name": "New",
    "last_name": "Person",
    "email": "new.person@jns.test",
    "password": "Str0ngPass!",
    "role_id": None,  # filled in setUpTestData once roles exist
    "availability": "Full-time",
}


class UserCreateApiTests(TestCase):
    @classmethod
    def setUpClass(cls):
        load_stored_procedures(
            "users/sp_get_session_user",
            "users/sp_create_user",
        )
        super().setUpClass()

    @classmethod
    def setUpTestData(cls):
        cls.admin_role = Role.objects.create(role_name="Admin")
        cls.manager_role = Role.objects.create(role_name="Manager")
        cls.employee_role = Role.objects.create(role_name="Employee")

        # The seed defines five system roles. The baseline used three; Intern
        # and Volunteer are added so every seeded role is covered.
        cls.intern_role = Role.objects.create(role_name="Intern")
        cls.volunteer_role = Role.objects.create(role_name="Volunteer")

        cls.org = cls._organisation("JNS Business Solutions")
        cls.other_org = cls._organisation("Unrelated Charity")

        cls.admin = cls._user(cls.org, "admin@jns.test", cls.admin_role)
        cls.manager = cls._user(cls.org, "manager@jns.test", cls.manager_role)

        cls.body = {**VALID_BODY, "role_id": cls.employee_role.role_id}

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
    def _user(org, email, role):
        return User.objects.create_user(
            email=email, organisation=org, role=role, password="Passw0rd!",
            first_name=email.split("@")[0].title(), last_name="Test", status="Active",
        )

    def _login_as(self, user):
        session = self.client.session
        session["user_id"] = user.user_id
        session.save()

    def _post(self, body):
        return self.client.post(URL, data=body, content_type="application/json")

    # -- authentication / authorisation -----------------------------------

    def test_no_session_returns_401(self):
        response = self._post(self.body)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_manager_returns_403(self):
        self._login_as(self.manager)

        response = self._post(self.body)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(User.objects.filter(email=self.body["email"]).exists())

    # -- success -----------------------------------------------------------

    def test_admin_creates_user_and_gets_safe_fields(self):
        self._login_as(self.admin)

        response = self._post(self.body)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        payload = response.json()

        self.assertEqual(payload["email"], "new.person@jns.test")
        self.assertEqual(payload["role_name"], "Employee")
        self.assertEqual(payload["status"], "Active")
        self.assertNotIn("password", payload)
        self.assertNotIn("password_hash", payload)

        created = User.objects.get(user_id=payload["user_id"])

        # Organisation came from the session, and the password was hashed
        # before it reached the procedure.
        self.assertEqual(created.organisation_id, self.org.organisation_id)
        self.assertNotEqual(created.password, self.body["password"])
        self.assertTrue(created.check_password(self.body["password"]))

    def test_organisation_in_body_is_ignored(self):
        self._login_as(self.admin)

        response = self._post({**self.body, "organisation_id": self.other_org.organisation_id})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created = User.objects.get(user_id=response.json()["user_id"])

        self.assertEqual(created.organisation_id, self.org.organisation_id)

    def test_availability_is_optional(self):
        self._login_as(self.admin)

        body = {k: v for k, v in self.body.items() if k != "availability"}
        response = self._post(body)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.json()["availability"])

    # -- validation --------------------------------------------------------

    def test_duplicate_email_in_organisation_returns_400(self):
        self._login_as(self.admin)

        response = self._post({**self.body, "email": "manager@jns.test"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.json())
        self.assertNotIn("Duplicate entry", str(response.content))

    def test_unknown_role_returns_400(self):
        self._login_as(self.admin)

        response = self._post({**self.body, "role_id": 999})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("role_id", response.json())
        self.assertNotIn("foreign key", str(response.content).lower())

    def test_missing_required_fields_returns_400(self):
        self._login_as(self.admin)

        response = self._post({"email": "only@jns.test"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        errors = response.json()

        for field in ("first_name", "last_name", "password", "role_id"):
            self.assertIn(field, errors)

    def test_short_password_returns_400(self):
        self._login_as(self.admin)

        response = self._post({**self.body, "password": "short"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.json())

    # -- added by the test owner ------------------------------------------
    #
    # The baseline covered the happy path and the obvious rejections. It did
    # not cover: the order in which the two rejections are decided, the three
    # non-privileged seeded roles, a stale session, the normalisation the
    # service performs on email and availability, the audit row the service
    # writes, or the serializer's deliberate decision not to trim passwords.

    def test_the_role_is_answered_before_the_body(self):
        """A caller with no permission should get 403, not 400.

        user_create.py calls serializer.is_valid(raise_exception=True) before
        create_user_in_organisation, so the body is validated first and the
        permission check only runs afterwards. An employee who posts an empty
        body therefore learns which fields the endpoint expects, even though
        the endpoint was never going to let them use it.

        This matters because the repository's own convention is 401 -> 403 ->
        400, which API 02 and the task endpoints follow: decide who you are,
        then whether you may, then whether the request is well formed. A 400
        here is a small information leak and an inconsistency between
        endpoints.

        The view now performs the permission check before serializer validation,
        so this test verifies the corrected 401 -> 403 -> 400 ordering.
        """

        employee = self._user(self.org, "employee@jns.test", self.employee_role)
        self._login_as(employee)

        response = self._post({})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_session_for_unknown_user_returns_401(self):
        """A session that outlived its user must not be treated as valid.

        sp_get_session_user returns nothing, the view flushes the session and
        answers 401. Only the no-session case was covered.
        """

        session = self.client.session
        session["user_id"] = 999999
        session.save()

        response = self._post(self.body)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(User.objects.filter(email=self.body["email"]).exists())

    def test_employee_intern_and_volunteer_cannot_create_users(self):
        """Only roles holding manage_users may create users.

        The baseline refused one role out of five. These are the other two
        non-privileged seeded roles plus Employee, so that a change to
        SYSTEM_ROLE_DEFAULTS cannot quietly widen who can add accounts.
        """

        cases = (
            ("employee@jns.test", self.employee_role),
            ("intern@jns.test", self.intern_role),
            ("volunteer@jns.test", self.volunteer_role),
        )

        for email, role in cases:
            with self.subTest(role=role.role_name):
                actor = self._user(self.org, email, role)
                self._login_as(actor)

                response = self._post({**self.body, "email": f"target.{role.role_id}@jns.test"})

                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
                self.assertFalse(
                    User.objects.filter(email=f"target.{role.role_id}@jns.test").exists()
                )

    def test_the_email_is_stored_trimmed_and_lowercased(self):
        """The service calls data["email"].strip().lower() before the insert.

        Login looks the address up in lower case, so an address stored with
        different case or stray whitespace would create an account nobody
        could sign in to. Nothing asserted the normalisation.
        """

        self._login_as(self.admin)

        response = self._post({**self.body, "email": "  Mixed.Case@JNS.Test  "})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["email"], "mixed.case@jns.test")

        created = User.objects.get(user_id=response.json()["user_id"])

        self.assertEqual(created.email, "mixed.case@jns.test")

    def test_duplicate_email_is_rejected_regardless_of_case(self):
        """Because the service lowercases first, the unique index still bites.

        The baseline proved an exact duplicate is refused. This proves the
        normalisation and the index work together, which is the case a user
        would actually hit when re-adding a colleague.
        """

        self._login_as(self.admin)

        response = self._post({**self.body, "email": "MANAGER@JNS.TEST"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.json())

    def test_blank_availability_is_stored_as_null(self):
        """`data.get("availability") or None` turns "" into NULL.

        The serializer allows a blank string, so the client may send one. The
        baseline only covered the field being absent, not present and empty,
        which would otherwise store "" and "unset" as two different things.
        """

        self._login_as(self.admin)

        response = self._post({**self.body, "availability": ""})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.json()["availability"])

        created = User.objects.get(user_id=response.json()["user_id"])

        self.assertIsNone(created.availability)

    def test_password_whitespace_is_not_trimmed(self):
        """The serializer sets trim_whitespace=False on password on purpose.

        DRF trims CharFields by default, which would silently change a
        password containing leading or trailing spaces and lock the user out
        of the account that was just created for them. Asserting it stops the
        flag being removed as tidying-up.
        """

        self._login_as(self.admin)

        raw = "  Str0ngPass!  "
        response = self._post({**self.body, "password": raw})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created = User.objects.get(user_id=response.json()["user_id"])

        self.assertTrue(created.check_password(raw))
        self.assertFalse(created.check_password(raw.strip()))

    def test_creating_a_user_writes_one_audit_row(self):
        """The service records history inside the same atomic block.

        Creating accounts is the change an auditor is most likely to ask
        about, and the row is written by the service rather than a signal, so
        a rewrite of the service could drop it with no other test noticing.
        """

        self._login_as(self.admin)

        before = AuditLog.objects.count()
        response = self._post(self.body)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AuditLog.objects.count(), before + 1)

        entry = AuditLog.objects.latest("audit_log_id")

        self.assertEqual(entry.entity_type, "User")
        self.assertEqual(entry.action, "Created")
        self.assertEqual(entry.entity_id, response.json()["user_id"])
        self.assertEqual(entry.entity_name, "New Person")
        self.assertEqual(entry.organisation_id, self.org.organisation_id)
        self.assertEqual(entry.user_id, self.admin.user_id)
        self.assertEqual(entry.new_value["email"], "new.person@jns.test")
        self.assertNotIn("password", entry.new_value)

    def test_a_rejected_create_writes_no_audit_row(self):
        """The history row must not survive a failed insert.

        record_history runs inside the same transaction.atomic() block as the
        insert, so a duplicate email should roll both back. If someone moves
        the recording outside the block, the audit log starts claiming users
        were created that do not exist.
        """

        self._login_as(self.admin)

        before = AuditLog.objects.count()
        response = self._post({**self.body, "email": "manager@jns.test"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(AuditLog.objects.count(), before)
