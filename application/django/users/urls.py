from django.urls import path

from users.api.login import LoginView
from users.api.session import SessionView
from users.api.logout import LogoutView
from users.api.user_list import UserListView

urlpatterns = [
    path("auth/login", LoginView.as_view(), name="login"),
    path("auth/session", SessionView.as_view(), name="session"),
    path("auth/logout", LogoutView.as_view(), name="logout"),
    path("users", UserListView.as_view(), name="user-list"),
]