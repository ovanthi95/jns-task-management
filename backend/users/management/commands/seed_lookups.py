from django.core.management.base import BaseCommand

from users.models import Role
from tasks.models import TaskType, TaskStatus, Priority


class Command(BaseCommand):
    help = "Create the initial global lookup data for WorkLink Cloud"

    def handle(self, *args, **options):

        # Roles
        roles = [
            ("Admin", "System and organisation administration"),
            ("Manager", "Project and task management"),
            ("Employee", "Standard employee access"),
            ("Intern", "Intern access"),
            ("Volunteer", "Volunteer access"),
        ]

        for role_name, description in roles:
            Role.objects.update_or_create(
                role_name=role_name,
                defaults={
                    "description": description,
                    "is_active": True,
                }
            )

        # Task types
        task_types = [
            ("Accounting", "Accounting-related work"),
            ("Taxation", "Tax-related work"),
            ("Funding Application", "Funding application work"),
        ]

        for order, (type_name, description) in enumerate(task_types, start=1):
            TaskType.objects.update_or_create(
                type_name=type_name,
                defaults={
                    "description": description,
                    "is_active": True,
                    "display_order": order,
                }
            )

        # Task workflow statuses
        statuses = [
            ("New", False),
            ("Assigned", False),
            ("In Progress", False),
            ("Waiting for Information", False),
            ("Under Review", False),
            ("Completed", True),
        ]

        for order, (status_name, is_terminal) in enumerate(statuses, start=1):
            TaskStatus.objects.update_or_create(
                status_name=status_name,
                defaults={
                    "is_active": True,
                    "is_terminal": is_terminal,
                    "display_order": order,
                }
            )

        # Priorities
        priorities = [
            ("Low", 1),
            ("Medium", 2),
            ("High", 3),
            ("Urgent", 4),
        ]

        for order, (priority_name, level) in enumerate(priorities, start=1):
            Priority.objects.update_or_create(
                priority_name=priority_name,
                defaults={
                    "priority_level": level,
                    "display_order": order,
                    "is_active": True,
                }
            )

        self.stdout.write(
            self.style.SUCCESS("Lookup data created successfully.")
        )