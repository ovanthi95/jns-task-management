# APIs 04/05 project endpoint
# Feature owner: Jessie

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from projects.api.project_create import ProjectCreateView
from projects.api.project_list import ProjectListView


@method_decorator(csrf_protect, name="dispatch")
class ProjectView(ProjectCreateView, ProjectListView):
    """
    Shared endpoint for:
    GET  /api/projects
    POST /api/projects
    """
    pass
