from django.urls import path

from users.api.login import LoginView
from users.api.logout import LogoutView
from users.api.role_management import RoleListCreateView, RoleUpdateView
from users.api.session import SessionView
from users.api.user_create import UserCreateView
from users.api.user_list import UserListView
from users.api.user_update import UserUpdateView
from users.api.workload import UserWorkloadTasksView, WorkloadView


class UserCollectionView(UserListView, UserCreateView):
    """/api/users: GET is API 02, POST is API 03."""


urlpatterns = [
    path("auth/login", LoginView.as_view(), name="login"),
    path("auth/session", SessionView.as_view(), name="session"),
    path("auth/logout", LogoutView.as_view(), name="logout"),
    path("users", UserCollectionView.as_view(), name="users"),
    path("users/<int:user_id>", UserUpdateView.as_view(), name="user-update"),
    path("roles", RoleListCreateView.as_view(), name="role-list-create"),
    path("roles/<int:role_id>", RoleUpdateView.as_view(), name="role-update"),
    path("workload", WorkloadView.as_view(), name="workload"),
    path(
        "workload/users/<int:user_id>/tasks",
        UserWorkloadTasksView.as_view(),
        name="user-workload-tasks",
    ),
]
