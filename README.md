# BookVerse Infrastructure

**Single consolidated infrastructure application** containing multiple packages for shared libraries and DevOps tooling across the BookVerse platform.

## 📦 Packages

This single infrastructure application publishes multiple packages:

### `bookverse-core` (Python Package)

Python commons library providing shared utilities for BookVerse services:
- **Authentication**: JWT/OIDC authentication with `AuthUser` and validation
- **Configuration**: Advanced YAML loading with deep merging and environment variables
- **API Utilities**: Standardized HTTP exceptions, pagination, and response helpers
- **Database**: SQLAlchemy session management and pagination utilities

### `bookverse-devops` (DevOps Package)

CI/CD workflows, scripts, and tooling for BookVerse services:
- **Reusable Workflows**: Standardized GitHub Actions workflows
- **Scripts**: Semantic versioning, evidence generation, and deployment utilities
- **Evidence Templates**: AppTrust evidence collection templates
- **Shared Tooling**: Common CI/CD patterns and configurations

## 🏗️ Repository Structure

```
bookverse-infra/
├── libraries/
│   ├── bookverse-core/          # Python commons library
│   └── bookverse-devops/        # CI/CD workflows & scripts
├── .github/workflows/           # Multi-library CI/CD
├── scripts/                     # Cross-library utilities
└── docs/                        # Documentation
```

## 🚀 Usage

### Using bookverse-core in Services

```python
# Authentication
from bookverse_core.auth import AuthUser, validate_jwt_token

# Configuration
from bookverse_core.config import ConfigLoader, load_config_with_defaults

# API Utilities
from bookverse_core.api.exceptions import raise_validation_error, raise_not_found_error

# Database
from bookverse_core.database import get_session, paginate_query
```

### Using bookverse-devops Workflows

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  build:
    uses: bookverse-infra/.github/workflows/shared-build.yml@main
    with:
      service_name: my-service
    secrets: inherit
```

## 📦 Publishing

Libraries are automatically built and published to JFrog Artifactory on:
- **Releases**: Full semantic versioning
- **Main branch**: Development versions
- **Pull requests**: Test builds

## 🔧 Development

### Local Development
```bash
# Install bookverse-core locally
pip install -e ./libraries/bookverse-core

# Run tests
pytest libraries/bookverse-core/tests
pytest libraries/bookverse-devops/tests
```

### Contributing
1. Make changes in the appropriate library directory
2. Update version numbers following semantic versioning
3. Add tests for new functionality
4. Submit pull request

## 📋 Migration Status

- ✅ **bookverse-recommendations**: Migrated to bookverse-core package
- ✅ **bookverse-inventory**: Migrated to bookverse-core package  
- ✅ **bookverse-checkout**: Migrated to bookverse-core package
- ✅ **bookverse-platform**: Migrated to bookverse-core package
- ⏳ **All services**: Migrating to published packages from bookverse-infra (in progress)

## 🏆 Benefits

- **Code Reuse**: Shared utilities across all BookVerse services
- **Consistency**: Standardized patterns and implementations
- **Maintainability**: Central location for common functionality
- **Quality**: Comprehensive testing and CI/CD for shared code
- **Security**: Centralized authentication and security patterns
