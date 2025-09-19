# Testing X-JFrog-Project Header Fix

This test validates that the missing X-JFrog-Project header fix resolves 
the HTTP 403 error when creating AppTrust application versions.

The header is required for OIDC token authentication with project-scoped 
permissions, following the pattern from recommendations service.

Test timestamp: Fri Sep 19 12:04:30 IDT 2025
