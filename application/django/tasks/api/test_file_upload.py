"""Tests for API 10 - POST /api/tasks/:taskId/files

Test owner: Manatka
Implementation owner: Manatka

S3 is never touched: get_s3_client is patched with a recording fake, so the
tests cover validation, the generated key, the S3 call, metadata persistence
and the cleanup rule without AWS credentials (playbook 9.3 / 18).

MySQL only; procedures are loaded before the class-level transaction.
"""

from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status

from data_access.sp_loader import load_stored_procedures
from projects.models import Project, ProjectMember
from tasks.models import Attachment, Priority, Task, TaskStatus, TaskType
from users.models import Organisation, Role, User

PATCH_TARGET = "tasks.services.file_upload_service.get_s3_client"


class RecordingS3Client:
    """Fake S3: records calls, optionally fails on put."""

    def __init__(self, fail_put=False):
        self.fail_put = fail_put
        self.puts = []
        self.deletes = []

    def put_object(self, Bucket, Key, Body, ContentType):
        if self.fail_put:
            raise RuntimeError("simulated S3 outage")
        self.puts.append({"Bucket": Bucket, "Key": Key, "size": len(Body), "ContentType": ContentType})

    def delete_object(self, Bucket, Key):
        self.deletes.append(Key)

    def generate_presigned_url(self, ClientMethod, Params, ExpiresIn):
        return f"https://download.test/{Params['Key']}?expires={ExpiresIn}"


def pdf(name="report.pdf", size=1024):
    return SimpleUploadedFile(name, b"%PDF-1.4 " + b"x" * size, content_type="application/pdf")


class FileUploadApiTests(TestCase):
    @classmethod
    def setUpClass(cls):
        load_stored_procedures(
            "users/sp_get_session_user",
            "tasks/sp_get_task_access",
            "tasks/sp_add_file",
            "tasks/sp_get_task_access",
            "tasks/sp_get_task_files",
        )
        super().setUpClass()

    @classmethod
    def setUpTestData(cls):
        cls.manager_role = Role.objects.create(role_name="Manager")
        cls.employee_role = Role.objects.create(role_name="Employee")

        cls.org = cls._organisation("JNS Business Solutions")
        cls.other_org = cls._organisation("Unrelated Charity")

        cls.member = cls._user(cls.org, "member@jns.test", cls.employee_role)
        cls.manager = cls._user(cls.org, "manager@jns.test", cls.manager_role)
        cls.outsider = cls._user(cls.org, "nobody@jns.test", cls.employee_role)  # same org, NOT a member

        cls.project = Project.objects.create(
            organisation=cls.org, project_name="Annual Accounts 2026", created_by=cls.manager,
        )
        ProjectMember.objects.create(project=cls.project, user=cls.member)
        ProjectMember.objects.create(project=cls.project, user=cls.manager)

        task_type = TaskType.objects.create(type_name="Accounting", display_order=1)
        task_status = TaskStatus.objects.create(status_name="New", display_order=1)
        priority = Priority.objects.create(priority_name="High", priority_level=3, display_order=1)

        cls.task = Task.objects.create(
            project=cls.project, task_type=task_type, status=task_status,
            priority=priority, title="Collect bank statements", created_by=cls.manager,
        )

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

    def _url(self, task_id=None):
        return f"/api/tasks/{task_id or self.task.task_id}/files"

    def _post(self, upload, task_id=None):
        return self.client.post(self._url(task_id), data={"file": upload} if upload else {})

    # -- authentication / access ------------------------------------------

    def test_no_session_returns_401(self):
        response = self._post(pdf())

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_member_returns_404(self):
        self._login_as(self.outsider)

        with patch(PATCH_TARGET, return_value=RecordingS3Client()) as fake:
            response = self._post(pdf())

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        fake.assert_not_called()  # access is checked before any upload

    def test_unknown_task_returns_404(self):
        self._login_as(self.member)

        with patch(PATCH_TARGET, return_value=RecordingS3Client()):
            response = self._post(pdf(), task_id=999999)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # -- validation --------------------------------------------------------

    def test_missing_file_returns_400(self):
        self._login_as(self.member)

        response = self._post(None)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.json())

    def test_disallowed_type_returns_400(self):
        self._login_as(self.member)
        exe = SimpleUploadedFile("virus.exe", b"MZ" + b"x" * 100, content_type="application/pdf")

        with patch(PATCH_TARGET, return_value=RecordingS3Client()) as fake:
            response = self._post(exe)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.json())
        fake.assert_not_called()

    def test_oversized_file_returns_400(self):
        self._login_as(self.member)

        with patch(PATCH_TARGET, return_value=RecordingS3Client()):
            response = self._post(pdf(size=10 * 1024 * 1024 + 1))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.json())

    # -- success -----------------------------------------------------------

    def test_member_uploads_and_metadata_is_stored(self):
        self._login_as(self.member)
        fake = RecordingS3Client()

        with patch(PATCH_TARGET, return_value=fake):
            response = self._post(pdf("Q3 report.pdf", size=2048))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        body = response.json()

        self.assertEqual(body["task_id"], self.task.task_id)
        self.assertEqual(body["file_name"], "Q3 report.pdf")
        self.assertEqual(body["file_type"], "application/pdf")
        self.assertEqual(body["uploaded_by"], self.member.user_id)
        self.assertTrue(body["s3_key"].startswith(f"tasks/{self.task.task_id}/"))
        self.assertTrue(body["s3_key"].endswith(".pdf"))
        self.assertNotIn("Q3 report", body["s3_key"])  # original name is not the key

        self.assertEqual(len(fake.puts), 1)
        self.assertEqual(fake.puts[0]["Key"], body["s3_key"])
        self.assertEqual(fake.puts[0]["ContentType"], "application/pdf")

        self.assertTrue(Attachment.objects.filter(task=self.task, s3_key=body["s3_key"]).exists())

    # -- consistency -------------------------------------------------------

    def test_storage_failure_returns_502_and_writes_nothing(self):
        self._login_as(self.member)

        with patch(PATCH_TARGET, return_value=RecordingS3Client(fail_put=True)):
            response = self._post(pdf())

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertFalse(Attachment.objects.filter(task=self.task).exists())

    def test_metadata_failure_deletes_uploaded_object(self):
        self._login_as(self.member)
        fake = RecordingS3Client()

        with patch(PATCH_TARGET, return_value=fake), \
             patch("tasks.services.file_upload_service.add_file", side_effect=RuntimeError("db down")):
            with self.assertRaises(RuntimeError):
                self._post(pdf())

        self.assertEqual(len(fake.puts), 1)
        self.assertEqual(fake.deletes, [fake.puts[0]["Key"]])

    def test_member_can_prepare_attachment_download(self):
        self._login_as(self.member)
        attachment = Attachment.objects.create(
            task=self.task,
            uploaded_by=self.member,
            file_name="Q3 report.pdf",
            file_type="application/pdf",
            file_size=2048,
            s3_key=f"tasks/{self.task.task_id}/report.pdf",
        )

        with patch(
            "tasks.services.file_upload_service.get_s3_client",
            return_value=RecordingS3Client(),
        ):
            response = self.client.get(
                f"/api/tasks/{self.task.task_id}/files/{attachment.attachment_id}/download"
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["file_name"], "Q3 report.pdf")
        self.assertIn("download.test", response.data["download_url"])

    def test_non_member_cannot_prepare_attachment_download(self):
        attachment = Attachment.objects.create(
            task=self.task,
            uploaded_by=self.member,
            file_name="Q3 report.pdf",
            file_type="application/pdf",
            file_size=2048,
            s3_key=f"tasks/{self.task.task_id}/report.pdf",
        )
        self._login_as(self.outsider)

        with patch(
            "tasks.services.file_upload_service.get_s3_client",
            return_value=RecordingS3Client(),
        ) as fake:
            response = self.client.get(
                f"/api/tasks/{self.task.task_id}/files/{attachment.attachment_id}/download"
            )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        fake.assert_not_called()
