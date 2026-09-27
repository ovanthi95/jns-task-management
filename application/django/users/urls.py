from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.urls import path

from users.api.login import LoginView
from users.api.session import SessionView
from users.api.logout import LogoutView
from users.api.user_list import UserListView
from users.api.user_create import UserCreateView


@method_decorator(csrf_protect, name="dispatch")
class UserCollectionView(UserListView, UserCreateView):
    """/api/users: GET is API 02 and POST is API 03."""


urlpatterns = [
    path("auth/login", LoginView.as_view(), name="login"),
    path("auth/session", SessionView.as_view(), name="session"),
    path("auth/logout", LogoutView.as_view(), name="logout"),
    path("users", UserCollectionView.as_view(), name="users"),
]
