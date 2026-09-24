from projects.api.project_create import ProjectCreateView
from projects.api.project_list import ProjectListView


class ProjectView(ProjectCreateView, ProjectListView):
    """
    Shared endpoint for:
    GET  /api/projects
    POST /api/projects
    """
    pass