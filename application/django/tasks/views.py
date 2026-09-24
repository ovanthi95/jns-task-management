"""Deliberately empty.

API 06 and API 07 used to be one ListCreateAPIView in this module, which read
and wrote through the Django ORM. Under the agreed layering an endpoint does
not reach the database at all, and the two services are separate files, so the
implementation moved:

    API 06  tasks/api/task_create.py
            tasks/services/task_create_service.py
            data_access/tasks/create_task.py
            data/stored_procedures/tasks/sp_create_task.sql

    API 07  tasks/api/task_list.py
            tasks/services/task_list_service.py
            data_access/tasks/get_project_tasks.py
            data/stored_procedures/tasks/sp_get_project_tasks.sql

The file is kept rather than deleted because Django creates it in every app
and its absence reads as an accident. Nothing should be added here: a new
endpoint belongs in tasks/api/.
"""
