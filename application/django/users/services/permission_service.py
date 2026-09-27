from users.models import Permission, Role, RolePermission


PERMISSION_CATALOG = [
    ("manage_users", "Manage users", "Create, edit and deactivate user accounts.", "Administration", 10),
    ("manage_roles", "Manage roles & permissions", "Create roles and configure their permissions.", "Administration", 20),
    ("view_all_projects", "View all projects", "See every project in the organisation.", "Projects", 10),
    ("create_projects", "Create projects", "Create new projects.", "Projects", 20),
    ("edit_projects", "Edit projects", "Edit project details and status.", "Projects", 30),
    ("view_all_tasks", "View all tasks", "See task details across organisation projects.", "Tasks", 10),
    ("create_tasks", "Create tasks", "Create tasks and choose an assignee.", "Tasks", 20),
    ("edit_tasks", "Edit task details", "Edit task title, dates, priority, type and estimates.", "Tasks", 30),
    ("reassign_tasks", "Reassign tasks", "Change the assignee of an existing task.", "Tasks", 40),
    ("change_any_task_status", "Change any task status", "Move any accessible task between workflow statuses.", "Tasks", 50),
    ("complete_assigned_tasks", "Complete assigned tasks", "Mark personally assigned tasks as Completed.", "Tasks", 60),
    ("send_task_notifications", "Send task assignment emails", "Email an assignee when a task is created.", "Tasks", 70),
    ("view_history", "View organisation history", "View the central Project, Task and User history.", "Reporting", 10),
    ("view_workload", "View workload", "View staff workload summaries and user workload details.", "Reporting", 20),
]

ALL_PERMISSION_CODES = {item[0] for item in PERMISSION_CATALOG}

SYSTEM_ROLE_DEFAULTS = {
    "admin": ALL_PERMISSION_CODES,
    "manager": {
        "view_all_projects",
        "create_projects",
        "edit_projects",
        "view_all_tasks",
        "create_tasks",
        "edit_tasks",
        "change_any_task_status",
        "complete_assigned_tasks",
        "view_workload",
    },
    "employee": {"complete_assigned_tasks"},
    "intern": {"complete_assigned_tasks"},
    "volunteer": {"complete_assigned_tasks"},
}


def default_permission_codes(role_name):
    return set(SYSTEM_ROLE_DEFAULTS.get(str(role_name or "").lower(), set()))


def role_permission_codes(role):
    if role is None:
        return set()

    if str(role.role_name or "").lower() == "admin":
        return set(ALL_PERMISSION_CODES)

    if not role.permissions_configured:
        return default_permission_codes(role.role_name)

    return set(
        role.role_permissions
        .filter(permission__is_active=True)
        .values_list("permission__code", flat=True)
    )


def actor_permission_codes(actor):
    if not actor:
        return set()

    supplied = actor.get("permissions")
    if supplied is not None:
        return set(supplied)

    role_name = actor.get("role_name")
    if str(role_name or "").lower() == "admin":
        return set(ALL_PERMISSION_CODES)

    role = None
    role_id = actor.get("role_id")

    if role_id:
        role = Role.objects.filter(role_id=role_id).first()
    elif role_name:
        role = Role.objects.filter(role_name__iexact=role_name).first()

    return role_permission_codes(role) if role else default_permission_codes(role_name)


def actor_has_permission(actor, code):
    return code in actor_permission_codes(actor)


def set_role_permissions(role, permission_codes):
    permission_codes = set(permission_codes)
    unknown = permission_codes - ALL_PERMISSION_CODES

    if unknown:
        raise ValueError(f"Unknown permissions: {', '.join(sorted(unknown))}")

    permissions = Permission.objects.filter(
        code__in=permission_codes,
        is_active=True,
    )

    RolePermission.objects.filter(role=role).delete()
    RolePermission.objects.bulk_create([
        RolePermission(role=role, permission=permission)
        for permission in permissions
    ])

    if not role.permissions_configured:
        role.permissions_configured = True
        role.save(update_fields=["permissions_configured", "updated_at"])


def ensure_default_permissions():
    permission_by_code = {}

    for code, label, description, category, order in PERMISSION_CATALOG:
        permission, _ = Permission.objects.update_or_create(
            code=code,
            defaults={
                "label": label,
                "description": description,
                "category": category,
                "display_order": order,
                "is_active": True,
            },
        )
        permission_by_code[code] = permission

    for role in Role.objects.all():
        if role.permissions_configured:
            continue

        codes = default_permission_codes(role.role_name)

        RolePermission.objects.bulk_create(
            [
                RolePermission(
                    role=role,
                    permission=permission_by_code[code],
                )
                for code in codes
            ],
            ignore_conflicts=True,
        )

        role.permissions_configured = True
        role.save(update_fields=["permissions_configured", "updated_at"])
