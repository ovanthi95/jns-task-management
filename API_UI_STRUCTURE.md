# JNS API and UI structure

Each API has its own backend module and test file. React UI, page logic, and API calls are separated so teammates can work with fewer merge conflicts.

| API | Endpoint | Code owner | Test owner | Backend module |
|---|---|---|---|---|
| 01 | POST /api/auth/login | Ovanthi | Manatka | users/api/login.py |
| 02 | GET /api/users | Manatka | Edward | users/api/user_list.py |
| 03 | POST /api/users | Manatka | Edward | users/api/user_create.py |
| 04 | POST /api/projects | Jesse | Edward | projects/api/project_create.py |
| 05 | GET /api/projects | Jesse | Manatka | projects/api/project_list.py |
| 06 | POST /api/projects/:projectId/tasks | Edward | Edward | tasks/api/task_create.py |
| 07 | GET /api/projects/:projectId/tasks | Edward | Jesse | tasks/api/task_list.py |
| 08 | PATCH /api/tasks/:taskId | Ovanthi | Manatka | tasks/api/task_update.py |
| 09 | POST /api/tasks/:taskId/comments | Ovanthi | Ovanthi | tasks/api/comment_create.py |
| 10 | POST /api/tasks/:taskId/files | Manatka | Manatka | tasks/api/file_upload.py |
| 11 | GET /api/tasks/:taskId/audit | Ovanthi | Jesse | audit/api/task_audit.py |
| 12 | PATCH /api/users/:userId | Ovanthi | Jesse | users/api/user_update.py |

Existing working code is not moved by this scaffold. In particular, API 06/07 remain in their current files until they are deliberately refactored and retested. Login.jsx is also left untouched because API 01 UI work is already in progress locally.
