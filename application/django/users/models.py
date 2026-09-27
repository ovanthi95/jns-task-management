from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


class Organisation(models.Model):
    organisation_id = models.AutoField(primary_key=True)
    organisation_name = models.CharField(max_length=150)
    organisation_type = models.CharField(max_length=50)
    email = models.EmailField(max_length=150)
    phone = models.CharField(max_length=30)
    address = models.CharField(max_length=255)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "organisations"

    def __str__(self):
        return self.organisation_name


class Permission(models.Model):
    permission_id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=80, unique=True)
    label = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True, default="")
    category = models.CharField(max_length=50)
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "permissions"
        ordering = ["category", "display_order", "label"]

    def __str__(self):
        return self.label


class Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    permissions_configured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "roles"

    def __str__(self):
        return self.role_name


class RolePermission(models.Model):
    role_permission_id = models.AutoField(primary_key=True)
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        db_column="role_id",
        related_name="role_permissions",
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        db_column="permission_id",
        related_name="role_permissions",
    )

    class Meta:
        db_table = "role_permissions"
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission"],
                name="unique_role_permission",
            )
        ]

    def __str__(self):
        return f"{self.role.role_name} - {self.permission.code}"


class UserManager(BaseUserManager):
    def create_user(self, email, organisation, role, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required.")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            organisation=organisation,
            role=role,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    user_id = models.AutoField(primary_key=True)

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.PROTECT,
        db_column="organisation_id",
        related_name="users"
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        db_column="role_id",
        related_name="users"
    )

    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    email = models.EmailField(max_length=150)
    password = models.CharField(max_length=255, db_column="password_hash")
    last_login = None
    availability = models.CharField(max_length=30, null=True, blank=True)
    status = models.CharField(max_length=20, default="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()
    USERNAME_FIELD = "user_id"

    class Meta:
        db_table = "users"
        constraints = [
            models.UniqueConstraint(
                fields=["organisation", "email"],
                name="unique_organisation_email"
            )
        ]

    @property
    def is_active(self):
        return self.status.lower() == "active"

    @property
    def is_staff(self):
        return (
            self.role is not None
            and self.role.role_name.lower() == "admin"
        )

    def has_perm(self, perm, obj=None):
        return self.is_staff

    def has_module_perms(self, app_label):
        return self.is_staff

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
