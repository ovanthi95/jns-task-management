# Stored Procedures

This folder contains the source-controlled SQL definitions for the JNS Task Management Platform.

Convention:
- One `.sql` file per stored procedure.
- One data-access function will call one stored procedure.
- Application/service functions may call multiple data-access functions.
- Plain-text passwords must never be stored or logged.
- Password verification remains in Django using Django's password hashing utilities.
