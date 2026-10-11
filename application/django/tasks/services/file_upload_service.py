# API 10 - File upload
# Owner: Manatka
#
# Orchestration: access check -> validate file -> upload to S3 -> record
# metadata. If the metadata write fails, the uploaded object is deleted so S3
# and the attachments table do not drift apart (playbook 9.3).
#
# S3 access goes through get_s3_client(). Locally and in tests that is a
# fake; on EC2 it is boto3 using the instance IAM role (playbook 18).
# boto3 is imported lazily so the module loads without it; it must be added to
# requirements.txt centrally before deployment.

import os
import uuid
from pathlib import PurePosixPath

from data_access.tasks.add_file import add_file
from data_access.tasks.get_task_access import get_task_access

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB, playbook section 18

# extension -> stored file_type. Content type from the browser is not trusted
# for the allow decision; the extension is the contract, the MIME is recorded.
ALLOWED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".csv": "text/csv",
    ".txt": "text/plain",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


class FileUploadValidationError(Exception):
    """A 400 with per-field messages, e.g. {"file": ["..."]}."""

    def __init__(self, field_errors):
        super().__init__("Validation failed")
        self.field_errors = field_errors


class TaskNotAccessible(Exception):
    """404: task missing, in another organisation, or caller not a member."""


class StorageError(Exception):
    """502: the object store rejected the upload."""


# -- S3 client ---------------------------------------------------------------

class LocalFakeS3Client:
    """In-memory stand-in for local development. Records calls, stores nothing."""

    def __init__(self):
        self.objects = {}

    def put_object(self, Bucket, Key, Body, ContentType):
        self.objects[(Bucket, Key)] = {"size": len(Body), "content_type": ContentType}

    def delete_object(self, Bucket, Key):
        self.objects.pop((Bucket, Key), None)

    def generate_presigned_url(self, ClientMethod, Params, ExpiresIn):
        return f"local://{Params['Key']}?expires={ExpiresIn}"


def get_bucket_name():
    return os.getenv("AWS_S3_BUCKET", "")


def get_s3_client():
    """Return an S3 client using the bucket's region, not the EC2 region."""

    if not get_bucket_name():
        return LocalFakeS3Client()

    import boto3
    from botocore.config import Config

    bucket_region = os.getenv("AWS_S3_REGION") or os.getenv("AWS_S3_BUCKET_REGION")

    if not bucket_region:
        # EC2 may run in a different AWS region from the S3 bucket.
        # Ask S3 for the bucket location using the global S3 endpoint.
        discovery = boto3.client("s3", region_name="us-east-1")
        location = discovery.get_bucket_location(
            Bucket=get_bucket_name()
        ).get("LocationConstraint")
        bucket_region = location or "us-east-1"

    return boto3.client(
        "s3",
        region_name=bucket_region,
        config=Config(signature_version="s3v4"),
    )


# -- validation --------------------------------------------------------------

def validate_upload(uploaded_file):
    """Return (extension, file_type) or raise FileUploadValidationError."""

    name = getattr(uploaded_file, "name", "") or ""
    extension = PurePosixPath(name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise FileUploadValidationError(
            {"file": ["File type not allowed. Allowed: PDF, DOC/DOCX, XLS/XLSX, CSV, TXT, PNG, JPG/JPEG."]}
        )

    size = getattr(uploaded_file, "size", None) or 0

    if size <= 0:
        raise FileUploadValidationError({"file": ["File is empty."]})

    if size > MAX_FILE_SIZE:
        raise FileUploadValidationError({"file": ["File is larger than 10 MB."]})

    return extension, ALLOWED_EXTENSIONS[extension]


def build_s3_key(task_id, extension):
    """A key we generate, never the client's filename as a path."""

    return f"tasks/{int(task_id)}/{uuid.uuid4().hex}{extension}"


# -- use case ----------------------------------------------------------------

def upload_task_file(session_user, task_id, uploaded_file):
    task = get_task_access(task_id, session_user["user_id"])

    if task is None:
        raise TaskNotAccessible()

    extension, file_type = validate_upload(uploaded_file)

    s3_key = build_s3_key(task_id, extension)
    bucket = get_bucket_name()
    client = get_s3_client()

    body = uploaded_file.read()

    try:
        client.put_object(Bucket=bucket, Key=s3_key, Body=body, ContentType=file_type)
    except Exception as exc:  # boto3 raises ClientError; the fake could raise anything
        raise StorageError("Upload to storage failed.") from exc

    try:
        return add_file(
            task_id=task["task_id"],
            uploaded_by=session_user["user_id"],
            file_name=PurePosixPath(uploaded_file.name).name[:255],
            file_type=file_type,
            file_size=len(body),
            s3_key=s3_key,
        )
    except Exception:
        # Deliberate consistency rule: no orphan objects in S3.
        try:
            client.delete_object(Bucket=bucket, Key=s3_key)
        except Exception:
            pass
        raise

def generate_download_url(attachment):
    """Generate a short-lived URL for an attachment the caller can already access."""
    bucket = get_bucket_name()

    if not bucket:
        raise StorageError("File storage is not configured.")

    client = get_s3_client()
    file_name = str(attachment.get("file_name") or "download").replace('"', "")
    file_type = attachment.get("file_type") or "application/octet-stream"

    try:
        return client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": bucket,
                "Key": attachment["s3_key"],
                "ResponseContentType": file_type,
                "ResponseContentDisposition": f'attachment; filename="{file_name}"',
            },
            ExpiresIn=300,
        )
    except Exception as exc:
        raise StorageError("Unable to prepare the file download.") from exc
