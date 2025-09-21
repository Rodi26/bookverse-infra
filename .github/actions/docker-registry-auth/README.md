# Docker Registry Authentication Action

A GitHub composite action that handles Docker registry authentication with JFrog using OIDC tokens.

## Overview

This action replaces the inline Docker authentication logic that was duplicated across multiple workflows. It provides a clean, reusable interface for authenticating Docker with JFrog registries using JWT tokens.

## Features

- ✅ **Secure token handling** with automatic secret masking
- ✅ **Configurable verbosity** levels (none, feedback, debug)
- ✅ **Input validation** with clear error messages
- ✅ **JWT token parsing** with multiple fallback strategies
- ✅ **Outputs** for downstream steps (registry host, username)
- ✅ **Debug mode** for troubleshooting authentication issues

## Usage

### Basic Usage

```yaml
- name: "[Build] Docker Registry Authentication"
  uses: ../../../bookverse-infra/.github/actions/docker-registry-auth@main
  with:
    oidc-token: ${{ steps.jfrog-cli-auth.outputs.oidc-token }}
    registry-url: ${{ vars.JFROG_URL }}
```

### With Debug Mode

```yaml
- name: "[Build] Docker Registry Authentication"
  uses: ../../../bookverse-infra/.github/actions/docker-registry-auth@main
  with:
    oidc-token: ${{ steps.jfrog-cli-auth.outputs.oidc-token }}
    registry-url: ${{ vars.JFROG_URL }}
    verbosity: 'debug'
```

### Using Outputs

```yaml
- name: "[Build] Docker Registry Authentication"
  id: docker-auth
  uses: ../../../bookverse-infra/.github/actions/docker-registry-auth@main
  with:
    oidc-token: ${{ steps.jfrog-cli-auth.outputs.oidc-token }}
    registry-url: ${{ vars.JFROG_URL }}

- name: "Use Authentication Info"
  run: |
    echo "Authenticated to registry: ${{ steps.docker-auth.outputs.registry-host }}"
    echo "Using username: ${{ steps.docker-auth.outputs.username }}"
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `oidc-token` | OIDC token for authentication | ✅ Yes | - |
| `registry-url` | JFrog registry URL | ✅ Yes | - |
| `verbosity` | Verbosity level: `none`, `feedback`, `debug` | ❌ No | `feedback` |

## Outputs

| Output | Description |
|--------|-------------|
| `registry-host` | The registry hostname that was authenticated |
| `username` | The username used for authentication |

## Verbosity Levels

- **`none`**: Silent operation, only errors are shown
- **`feedback`**: Standard operation messages (default)
- **`debug`**: Detailed logging including token parsing steps and authentication details

## Migration from Inline Code

This action replaces the previous 45+ line inline Docker authentication blocks. To migrate:

**Before:**
```yaml
- name: "[Build] Docker Registry Authentication"
  run: |
    set -euo pipefail
    echo "🔐 Authenticating Docker with JFrog registry..."
    # ... 40+ lines of JWT parsing and docker login logic
```

**After:**
```yaml
- name: "[Build] Docker Registry Authentication"
  uses: ../../../bookverse-infra/.github/actions/docker-registry-auth@main
  with:
    oidc-token: ${{ steps.jfrog-cli-auth.outputs.oidc-token }}
    registry-url: ${{ vars.JFROG_URL }}
    verbosity: 'feedback'
```

## Benefits

- **95% code reduction** per workflow (45+ lines → 5 lines)
- **Eliminates duplication** across all service workflows
- **Better security** with automatic secret masking
- **Consistent verbosity** across all services
- **Centralized maintenance** and updates
- **Better error handling** and validation

## Troubleshooting

If authentication fails, enable debug mode:

```yaml
verbosity: 'debug'
```

This will show:
- JWT token parsing details
- Registry hostname extraction
- Username extraction process
- Authentication attempt details

## Dependencies

- `jq` - for JSON parsing (available in GitHub Actions runners)
- `base64` - for JWT token decoding (available in GitHub Actions runners)
- `docker` - for registry login (available in GitHub Actions runners)
