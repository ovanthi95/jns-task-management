"""Integration tests for API 08 - PATCH /api/tasks/:taskId.

These tests use the real MySQL stored procedures. They cover the Trello card's
required cases: valid update, forbidden fields, role/assignee rules and
not-found handling, plus validation and task-history persistence.

Run from application/django with DB_ENGINE=mysql:

    python manage.py test tasks.api.test_task_update
"""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from data_access.sp_loader import load_stored_procedures
from projects.models import Project, ProjectMember
from tasks.models import (
    Priority,
    Task,
    TaskAssignee,
    TaskHistory,
    TaskStatus,
    TaskType,
)
from users.models import Organisation, Role, User


class TaskUpdateApiTests(TestCase):
    @classmethod
    def setUpClass(cls):
        # CREATE PROCEDURE implicitly commits in MySQL, so load before
        # TestCase opens the class-level transaction.
        load_stored_procedures(
            "users/sp_get_session_user",
            "tasks/sp_get_task_access",
            "tasks/sp_get_project_tasks",
            "tasks/sp_get_project_user_access",
            "tasks/sp_check_task_lookups",
            "tasks/sp_get_task_status",
            "tasks/sp_update_task",
        )
        super().setUpClass()

    def setUp(self):
        self.admin_role = Role.objects.create(role_name="Admin")
        self.manager_role = Role.objects.create(role_name="Manager")
        self.employee_role = Role.objects.create(role_name="Employee")
        self.intern_role = Role.objects.create(role_name="Intern")
        self.volunteer_role = Role.objects.create(role_name="Volunteer")

        self.org = self._organisation("JNS Business Solutions")
        self.other_org = self._organisation("Unrelated Charity")

        self.admin = self._user(
            self.org,
            "admin@jns.test",
            self.admin_role,
            "Admin",
            "User",
        )
        self.manager = self._user(
            self.org,
            "manager@jns.test",
            self.manager_role,
            "Manager",
            "User",
        )
        self.worker = self._user(
            self.org,
            "worker@jns.test",
            self.employee_role,
            "Jane",
            "Smith",
        )
        self.replacement = self._user(
            self.org,
            "replacement@jns.test",
            self.employee_role,
            "Alex",
            "Taylor",
        )
        self.observer = self._user(
            self.org,
            "observer@jns.test",
            self.employee_role,
            "Observer",
            "User",
        )
        self.non_member = self._user(
            self.org,
            "nonmember@jns.test",
            self.manager_role,
            "Non",
            "Member",
        )
        self.other_user = self._user(
            self.other_org,
            "other@example.test",
            self.manager_role,
            "Other",
            "User",
        )

        self.project = Project.objects.create(
            organisation=self.org,
            project_name="Annual Accounts 2026",
            created_by=self.manager,
        )

        for user in (
            self.admin,
            self.manager,
            self.worker,
            self.replacement,
            self.observer,
        ):
            ProjectMember.objects.create(project=self.project, user=user)

        self.task_type = TaskType.objects.create(
            type_name="Accounting",
            display_order=1,
        )
        self.other_task_type = TaskType.objects.create(
            type_name="Taxation",
            display_order=2,
        )

        self.new_status = TaskStatus.objects.create(
            status_name="New",
            display_order=1,
        )
        self.progress_status = TaskStatus.objects.create(
            status_name="In Progress",
            display_order=2,
        )
        self.completed_status = TaskStatus.objects.create(
            status_name="Completed",
            display_order=3,
            is_terminal=True,
        )

        self.high_priority = Priority.objects.create(
            priority_name="High",
            priority_level=3,
            display_order=1,
        )
        self.low_priority = Priority.objects.create(
            priority_name="Low",
            priority_level=1,
            display_order=2,
        )

        self.task = Task.objects.create(
            project=self.project,
            task_type=self.task_type,
            status=self.new_status,
            priority=self.high_priority,
            title="Collect bank statements",
            description="Original description",
            start_date="2026-10-01",
            due_date="2026-10-20",
            estimated_hours="4.00",
            created_by=self.manager,
        )

        TaskAssignee.objects.create(
            task=self.task,
            user=self.worker,
            assigned_by=self.manager,
        )

        self.url = f"/api/tasks/{self.task.task_id}"
        self.client = APIClient()

    # ------------------------------------------------------------ auth/access

    def test_no_session_returns_401(self):
        response = self.client.patch(
            self.url,
            {"title": "Changed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_custom_jns_session_authenticates_the_patch(self):
        self._login_as(self.manager)

        response = self.client.patch(
            self.url,
            {"title": "Updated through session"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated through session")

    def test_unknown_task_returns_404(self):
        self._login_as(self.manager)

        response = self.client.patch(
            "/api/tasks/999999",
            {"title": "Changed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_same_organisation_non_member_returns_404(self):
        self._login_as(self.non_member)

        response = self.client.patch(
            self.url,
            {"title": "Changed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ------------------------------------------------------------ valid update

    def test_manager_can_update_permitted_task_details(self):
        self._login_as(self.manager)

        response = self.client.patch(
            self.url,
            {
                "title": "Prepare GST return",
                "task_type_id": self.other_task_type.pk,
                "priority_id": self.low_priority.pk,
                "due_date": "2026-10-25",
                "estimated_hours": "6.50",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Prepare GST return")
        self.assertEqual(response.data["task_type_id"], self.other_task_type.pk)
        self.assertEqual(response.data["priority_id"], self.low_priority.pk)
        self.assertEqual(response.data["due_date"], "2026-10-25")
        self.assertEqual(response.data["estimated_hours"], "6.50")

        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Prepare GST return")
        self.assertEqual(self.task.task_type_id, self.other_task_type.pk)
        self.assertEqual(self.task.priority_id, self.low_priority.pk)

    def test_manager_can_change_any_task_status(self):
        self._login_as(self.manager)

        response = self.client.patch(
            self.url,
            {"status_id": self.progress_status.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status_id"], self.progress_status.pk)
        self.assertEqual(response.data["status_name"], "In Progress")

    def test_admin_can_reassign_to_existing_project_member(self):
        self._login_as(self.admin)

        response = self.client.patch(
            self.url,
            {"assignee_id": self.replacement.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [person["user_id"] for person in response.data["assignees"]],
            [self.replacement.pk],
        )
        self.assertTrue(
            TaskAssignee.objects.filter(
                task=self.task,
                user=self.replacement,
            ).exists()
        )
        self.assertFalse(
            TaskAssignee.objects.filter(
                task=self.task,
                user=self.worker,
            ).exists()
        )

    # ------------------------------------------------------------ permissions

    def test_manager_cannot_reassign_a_task(self):
        self._login_as(self.manager)

        response = self.client.patch(
            self.url,
            {"assignee_id": self.replacement.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(
            TaskAssignee.objects.filter(
                task=self.task,
                user=self.worker,
            ).exists()
        )

    def test_assigned_employee_can_mark_own_task_completed(self):
        self._login_as(self.worker)

        response = self.client.patch(
            self.url,
            {"status_id": self.completed_status.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status_name"], "Completed")

    def test_assigned_employee_can_change_own_task_to_any_status(self):
        self._login_as(self.worker)

        response = self.client.patch(
            self.url,
            {"status_id": self.progress_status.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status_name"], "In Progress")

    def test_assigned_employee_cannot_change_another_users_task_status(self):
        other_task = Task.objects.create(
            project=self.project,
            task_type=self.task_type,
            status=self.new_status,
            priority=self.high_priority,
            title="Other user's task",
            created_by=self.manager,
        )
        TaskAssignee.objects.create(
            task=other_task,
            user=self.observer,
            assigned_by=self.manager,
        )

        self._login_as(self.worker)

        response = self.client.patch(
            f"/api/tasks/{other_task.task_id}",
            {"status_id": self.progress_status.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_assigned_employee_cannot_edit_task_details(self):
        self._login_as(self.worker)

        response = self.client.patch(
            self.url,
            {"title": "Employee changed this"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Collect bank statements")

    def test_project_member_who_is_not_assignee_cannot_complete_task(self):
        self._login_as(self.observer)

        response = self.client.patch(
            self.url,
            {"status_id": self.completed_status.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ------------------------------------------------------------ forbidden fields

    def test_forbidden_fields_are_rejected_instead_of_ignored(self):
        self._login_as(self.admin)

        response = self.client.patch(
            self.url,
            {
                "project_id": 999,
                "created_by": self.admin.pk,
                "actual_hours": "99.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        for field in ("project_id", "created_by", "actual_hours"):
            self.assertIn(field, response.data)

        self.task.refresh_from_db()
        self.assertEqual(self.task.project_id, self.project.pk)
        self.assertEqual(self.task.created_by_id, self.manager.pk)
        self.assertIsNone(self.task.actual_hours)

    def test_empty_patch_is_rejected(self):
        self._login_as(self.manager)

        response = self.client.patch(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------ validation

    def test_invalid_priority_returns_400(self):
        self._login_as(self.manager)

        response = self.client.patch(
            self.url,
            {"priority_id": 999999},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("priority_id", response.data)

    def test_invalid_status_returns_400(self):
        self._login_as(self.manager)

        response = self.client.patch(
            self.url,
            {"status_id": 999999},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status_id", response.data)

    def test_admin_cannot_assign_same_org_user_who_is_not_project_member(self):
        self._login_as(self.admin)

        response = self.client.patch(
            self.url,
            {"assignee_id": self.non_member.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("assignee_id", response.data)

    def test_due_date_cannot_be_before_existing_start_date(self):
        self._login_as(self.manager)

        response = self.client.patch(
            self.url,
            {"due_date": "2026-09-30"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("due_date", response.data)

    def test_blank_title_returns_400(self):
        self._login_as(self.manager)

        response = self.client.patch(
            self.url,
            {"title": "   "},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)

    # ------------------------------------------------------------ history

    def test_changed_fields_are_written_to_task_history(self):
        self._login_as(self.manager)

        response = self.client.patch(
            self.url,
            {
                "title": "Updated title",
                "priority_id": self.low_priority.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        history = TaskHistory.objects.filter(
            task=self.task,
        ).order_by("history_id")

        self.assertEqual(
            list(history.values_list("field_name", flat=True)),
            ["title", "priority_id"],
        )

        self.assertTrue(
            all(row.changed_by_id == self.manager.pk for row in history)
        )

    def test_unchanged_value_does_not_create_history_row(self):
        self._login_as(self.manager)

        response = self.client.patch(
            self.url,
            {"title": self.task.title},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(TaskHistory.objects.filter(task=self.task).exists())


    # ------------------------------------------------------------ test-owner additions (Manatka)

    def test_user_from_other_organisation_cannot_authenticate(self):
        # Single-organisation deployment: sp_get_session_user only resolves
        # JNS users, so a session for another organisation is rejected at the
        # auth layer (401) before any task lookup.
        self._login_as(self.other_user)

        response = self.client.patch(self.url, {"title": "Changed"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Collect bank statements")

    def test_admin_can_update_task_details(self):
        self._login_as(self.admin)

        response = self.client.patch(
            self.url,
            {"title": "Admin edited", "priority_id": self.low_priority.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Admin edited")
        self.assertEqual(response.data["priority_id"], self.low_priority.pk)

    def test_assigned_employee_cannot_reassign(self):
        self._login_as(self.worker)

        response = self.client.patch(
            self.url, {"assignee_id": self.replacement.pk}, format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(TaskAssignee.objects.filter(task=self.task, user=self.worker).exists())

    def test_invalid_task_type_returns_400(self):
        self._login_as(self.manager)

        response = self.client.patch(self.url, {"task_type_id": 999999}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("task_type_id", response.data)

    def test_negative_estimated_hours_returns_400(self):
        self._login_as(self.manager)

        response = self.client.patch(self.url, {"estimated_hours": "-1.00"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("estimated_hours", response.data)

    # ------------------------------------------------------------ helpers

    def _login_as(self, user):
        session = self.client.session
        session["user_id"] = user.user_id
        session.save()

    @staticmethod
    def _organisation(name):
        return Organisation.objects.create(
            organisation_name=name,
            organisation_type="SME",
            email=f"info-{name.split()[0].lower()}@example.test",
            phone="09-000-0000",
            address="Auckland",
            status="Active",
        )

    @staticmethod
    def _user(org, email, role, first_name, last_name):
        return User.objects.create_user(
            email=email,
            organisation=org,
            role=role,
            password="Passw0rd!",
            first_name=first_name,
            last_name=last_name,
            status="Active",
        )
