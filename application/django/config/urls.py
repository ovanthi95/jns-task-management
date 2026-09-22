from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path('admin/', admin.site.urls),

    # The agreed REST list is served under /api/ with no version segment.
    # Each app registers its own routes; this file only mounts them.
    path('api/', include('users.urls')),
    path('api/', include('tasks.urls')),
]