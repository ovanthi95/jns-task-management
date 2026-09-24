"""Failures the task services raise, and what each one means.

Owner: Edward

The services decide *what* went wrong. The endpoint modules decide which HTTP
status says so. Keeping the two apart is why these are plain exceptions rather
than DRF exceptions: a service can be called from a management command or
another service without dragging an HTTP response class along with it.

    ProjectNotVisible   -> 404
    RoleNotPermitted    -> 403
    InvalidTaskInput    -> 400
"""


class TaskServiceError(Exception):
    """Base class, so a caller can catch every service failure at once."""


class ProjectNotVisible(TaskServiceError):
    """The project does not exist, or this caller may not see that it does.

    Deliberately one exception for three different situations: no such
    project, a project in another organisation, and a project the caller is
    not a member of. They are answered identically so that a 404 cannot be
    used to prove a project exists in a tenant the caller cannot reach.
    """


class RoleNotPermitted(TaskServiceError):
    """The caller's role is not allowed to perform this action.

    Unlike ProjectNotVisible this is a property of the caller alone, so saying
    so out loud leaks nothing about anyone else's data.
    """

    def __init__(self, message="Your role is not permitted to create tasks."):
        super().__init__(message)
        self.message = message


class InvalidTaskInput(TaskServiceError):
    """A business rule rejected the request body.

    `errors` is keyed by the field name the client sent, so the endpoint can
    hand it back in the same shape the serializer uses for its own errors.
    """

    def __init__(self, errors):
        super().__init__(errors)
        self.errors = errors
