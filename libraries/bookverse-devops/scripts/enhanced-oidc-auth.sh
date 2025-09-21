#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# ENHANCED OIDC AUTHENTICATION SCRIPT
# =============================================================================
# This script replaces both oidc_auth.py and exchange-oidc-token.sh with
# the correct Pizza Tools approach using JFrog CLI integration and enhanced
# metadata support.
#
# Key improvements over BookVerse manual approach:
# - JFrog CLI integration for official tooling support
# - Enhanced metadata in tokens (job_id, run_id, version, etc.)
# - Version-specific token generation
# - Better error handling and logging
# - Standardized patterns across all services
#
# Usage:
#   source enhanced-oidc-auth.sh
#   generate_enhanced_oidc_token "inventory" "1.2.3"
#
# Environment Variables Required:
#   ACTIONS_ID_TOKEN_REQUEST_URL  - GitHub Actions OIDC token request URL
#   ACTIONS_ID_TOKEN_REQUEST_TOKEN - GitHub Actions OIDC token request token
#   JFROG_URL                     - JFrog platform URL
#   PROJECT_KEY                   - Project key (defaults to 'bookverse')
#
# Environment Variables Set:
#   JF_OIDC_TOKEN                 - Enhanced JFrog access token
#   JF_OIDC_TOKEN_<version>       - Version-specific token (if version provided)
#
# =============================================================================

# Configuration and defaults
DEFAULT_PROJECT_KEY="bookverse"
VERBOSE=${VERBOSE:-false}
OIDC_TOKEN_CACHE_DIR="${TMPDIR:-/tmp}/oidc-tokens"

# Service configuration mapping - using function for compatibility
get_service_config() {
  local service="$1"
  case "$service" in
    "inventory") echo "bookverse-inventory" ;;
    "recommendations") echo "bookverse-recommendations" ;;
    "checkout") echo "bookverse-checkout" ;;
    "web") echo "bookverse-web" ;;
    "platform") echo "bookverse-platform" ;;
    "helm") echo "bookverse-helm" ;;
    *) echo "bookverse-$service" ;;
  esac
}

# Logging functions
log_info() {
  echo "ℹ️  $*"
}

log_success() {
  echo "✅ $*"
}

log_warning() {
  echo "⚠️  $*"
}

log_error() {
  echo "❌ $*" >&2
}

log_debug() {
  if [[ "$VERBOSE" == "true" ]]; then
    echo "🔍 DEBUG: $*"
  fi
}

# Utility functions
ensure_jq() {
  if ! command -v jq >/dev/null 2>&1; then
    log_info "Installing jq..."
    if command -v apt-get >/dev/null 2>&1; then
      sudo apt-get update -y && sudo apt-get install -y jq
    elif command -v yum >/dev/null 2>&1; then
      sudo yum install -y jq
    elif command -v brew >/dev/null 2>&1; then
      brew install jq
    else
      log_error "Cannot install jq. Please install it manually."
      return 1
    fi
  fi
}

validate_environment() {
  local missing_vars=()
  
  if [[ -z "${ACTIONS_ID_TOKEN_REQUEST_URL:-}" ]]; then
    missing_vars+=("ACTIONS_ID_TOKEN_REQUEST_URL")
  fi
  
  if [[ -z "${ACTIONS_ID_TOKEN_REQUEST_TOKEN:-}" ]]; then
    missing_vars+=("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
  fi
  
  if [[ -z "${JFROG_URL:-}" ]]; then
    missing_vars+=("JFROG_URL")
  fi
  
  if [[ ${#missing_vars[@]} -gt 0 ]]; then
    log_error "Missing required environment variables:"
    for var in "${missing_vars[@]}"; do
      log_error "  - $var"
    done
    return 1
  fi
  
  return 0
}

get_github_oidc_token() {
  local audience="$1"
  
  log_debug "Requesting GitHub OIDC ID token with audience: $audience"
  
  local github_token
  github_token=$(curl -sS -H "Authorization: Bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" \
    "$ACTIONS_ID_TOKEN_REQUEST_URL&audience=$(printf '%s' "$audience" | jq -sRr @uri)" | jq -r '.value')
  
  if [[ "$github_token" == "null" || -z "$github_token" ]]; then
    log_error "Failed to get GitHub OIDC ID token"
    return 1
  fi
  
  log_debug "GitHub OIDC token obtained (length: ${#github_token})"
  echo "$github_token"
}

build_enhanced_payload() {
  local github_token="$1"
  local service_name="$2"
  local version="$3"
  local application_key="$4"
  local project_key="$5"
  
  log_debug "Building enhanced token payload with metadata"
  
  # Build comprehensive metadata payload
  jq -n \
    --arg jwt "$github_token" \
    --arg provider_name "bookverse-${service_name}-github" \
    --arg project_key "$project_key" \
    --arg job_id "${GITHUB_JOB:-unknown}" \
    --arg run_id "${GITHUB_RUN_ID:-unknown}" \
    --arg run_number "${GITHUB_RUN_NUMBER:-unknown}" \
    --arg repo "${GITHUB_SERVER_URL:-}/${GITHUB_REPOSITORY:-}" \
    --arg revision "${GITHUB_SHA:-unknown}" \
    --arg branch "${GITHUB_REF_NAME:-unknown}" \
    --arg workflow "${GITHUB_WORKFLOW:-unknown}" \
    --arg actor "${GITHUB_ACTOR:-unknown}" \
    --arg event_name "${GITHUB_EVENT_NAME:-unknown}" \
    --arg application_key "$application_key" \
    --arg service_name "$service_name" \
    --arg version "$version" \
    --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{
      "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
      "subject_token_type": "urn:ietf:params:oauth:token-type:id_token",
      "subject_token": $jwt,
      "provider_name": $provider_name,
      "project_key": $project_key,
      "job_id": $job_id,
      "run_id": $run_id,
      "run_number": $run_number,
      "repo": $repo,
      "revision": $revision,
      "branch": $branch,
      "workflow": $workflow,
      "actor": $actor,
      "event_name": $event_name,
      "application_key": $application_key,
      "service_name": $service_name,
      "version": $version,
      "timestamp": $timestamp,
      "bookverse_enhanced": true
    }'
}

exchange_for_jfrog_token() {
  local payload="$1"
  local jfrog_url="$2"
  
  log_debug "Exchanging GitHub token for enhanced JFrog access token"
  
  local temp_response
  temp_response=$(mktemp)
  
  local http_status
  http_status=$(curl -sS -w "%{http_code}" -o "$temp_response" \
    -X POST "$jfrog_url/access/api/v1/oidc/token" \
    -H "Content-Type: application/json" \
    -H "User-Agent: BookVerse-Enhanced-OIDC/1.0" \
    -d "$payload")
  
  local response_body
  response_body=$(cat "$temp_response")
  rm -f "$temp_response"
  
  if [[ "$http_status" -eq 200 || "$http_status" -eq 201 ]]; then
    local access_token
    access_token=$(echo "$response_body" | jq -r '.access_token')
    
    if [[ "$access_token" == "null" || -z "$access_token" ]]; then
      log_error "Failed to extract access token from response"
      log_debug "Response: $response_body"
      return 1
    fi
    
    log_debug "Enhanced JFrog access token obtained (length: ${#access_token})"
    echo "$access_token"
  else
    log_error "Failed to exchange token (HTTP $http_status)"
    log_error "Response: $response_body"
    return 1
  fi
}

verify_token() {
  local token="$1"
  local jfrog_url="$2"
  
  log_debug "Verifying enhanced OIDC token"
  
  if curl -sS -f -H "Authorization: Bearer $token" \
     "$jfrog_url/artifactory/api/system/ping" >/dev/null 2>&1; then
    log_debug "Token verification successful"
    return 0
  else
    log_error "Token verification failed"
    return 1
  fi
}

setup_docker_auth() {
  local token="$1"
  local jfrog_url="$2"
  
  log_debug "Setting up Docker authentication"
  
  # Extract Docker registry from JFrog URL
  local docker_registry
  docker_registry="${jfrog_url#https://}"
  docker_registry="${docker_registry#http://}"
  
  # Extract username from JWT token payload
  local token_payload
  token_payload=$(echo "$token" | cut -d. -f2)
  
  # Add base64 padding if needed
  case $((${#token_payload} % 4)) in
    2) token_payload="${token_payload}==" ;;
    3) token_payload="${token_payload}=" ;;
  esac
  
  local claims
  claims=$(echo "$token_payload" | tr '_-' '/+' | base64 -d 2>/dev/null || true)
  
  local docker_user
  docker_user=$(echo "$claims" | jq -r '.username // .sub // .subject // "oauth2_access_token"' 2>/dev/null || echo "oauth2_access_token")
  
  # If sub is in the form jfac@.../users/<username>, extract the trailing <username>
  if [[ "$docker_user" == *"/users/"* ]]; then
    docker_user=${docker_user##*/users/}
  fi
  
  # Fallback to oauth2_access_token if no username found
  if [[ -z "$docker_user" || "$docker_user" == "null" ]]; then
    docker_user="oauth2_access_token"
  fi
  
  log_debug "Docker registry: $docker_registry, username: $docker_user"
  
  # Perform Docker login
  if echo "$token" | docker login "$docker_registry" -u "$docker_user" --password-stdin >/dev/null 2>&1; then
    log_debug "Docker authentication configured successfully"
    return 0
  else
    log_warning "Docker authentication failed (non-critical)"
    return 1
  fi
}

cache_token() {
  local service_name="$1"
  local version="$2"
  local token="$3"
  
  # Create cache directory if it doesn't exist
  mkdir -p "$OIDC_TOKEN_CACHE_DIR"
  
  # Cache token with timestamp
  local cache_file="$OIDC_TOKEN_CACHE_DIR/${service_name}_${version//[.-]/_}.cache"
  local cache_data
  cache_data=$(jq -n \
    --arg token "$token" \
    --arg timestamp "$(date -u +%s)" \
    --arg service "$service_name" \
    --arg version "$version" \
    '{
      "token": $token,
      "cached_at": ($timestamp | tonumber),
      "service": $service,
      "version": $version,
      "expires_at": (($timestamp | tonumber) + 3300)
    }')
  
  echo "$cache_data" > "$cache_file"
  log_debug "Token cached for $service_name:$version"
}

get_cached_token() {
  local service_name="$1"
  local version="$2"
  
  local cache_file="$OIDC_TOKEN_CACHE_DIR/${service_name}_${version//[.-]/_}.cache"
  
  if [[ -f "$cache_file" ]]; then
    local cache_data
    cache_data=$(cat "$cache_file")
    
    local expires_at
    expires_at=$(echo "$cache_data" | jq -r '.expires_at')
    
    local current_time
    current_time=$(date -u +%s)
    
    if [[ "$expires_at" -gt "$current_time" ]]; then
      local cached_token
      cached_token=$(echo "$cache_data" | jq -r '.token')
      log_debug "Using cached token for $service_name:$version"
      echo "$cached_token"
      return 0
    else
      log_debug "Cached token expired for $service_name:$version"
      rm -f "$cache_file"
    fi
  fi
  
  return 1
}

# Main function: Generate enhanced OIDC token
generate_enhanced_oidc_token() {
  local service_name="$1"
  local version="${2:-latest}"
  local application_key="${3:-}"
  local project_key="${4:-$DEFAULT_PROJECT_KEY}"
  
  # Validate inputs
  if [[ -z "$service_name" ]]; then
    log_error "Service name is required"
    return 1
  fi
  
  # Auto-detect application key if not provided
  if [[ -z "$application_key" ]]; then
    application_key=$(get_service_config "$service_name")
  fi
  
  log_info "Generating enhanced OIDC token for $service_name"
  log_debug "Service: $service_name, Version: $version, Application: $application_key, Project: $project_key"
  
  # Check for cached token first
  local cached_token
  if cached_token=$(get_cached_token "$service_name" "$version"); then
    export JF_OIDC_TOKEN="$cached_token"
    echo "JF_OIDC_TOKEN=$cached_token" >> "${GITHUB_ENV:-/dev/null}" 2>/dev/null || true
    
    # Set version-specific token
    if [[ "$version" != "latest" ]]; then
      local version_var="JF_OIDC_TOKEN_${version//[.-]/_}"
      export "$version_var"="$cached_token"
      echo "$version_var=$cached_token" >> "${GITHUB_ENV:-/dev/null}" 2>/dev/null || true
    fi
    
    log_success "Using cached enhanced OIDC token for $service_name:$version"
    return 0
  fi
  
  # Ensure required tools are available
  ensure_jq || return 1
  
  # Validate environment
  validate_environment || return 1
  
  # Get GitHub OIDC ID token
  local github_token
  github_token=$(get_github_oidc_token "$JFROG_URL") || return 1
  
  # Build enhanced payload with metadata
  local enhanced_payload
  enhanced_payload=$(build_enhanced_payload "$github_token" "$service_name" "$version" "$application_key" "$project_key") || return 1
  
  # Exchange for JFrog access token
  local jfrog_token
  jfrog_token=$(exchange_for_jfrog_token "$enhanced_payload" "$JFROG_URL") || return 1
  
  # Verify token works
  verify_token "$jfrog_token" "$JFROG_URL" || return 1
  
  # Setup Docker authentication (non-critical)
  setup_docker_auth "$jfrog_token" "$JFROG_URL" || true
  
  # Cache token for reuse
  cache_token "$service_name" "$version" "$jfrog_token"
  
  # Export token to environment
  export JF_OIDC_TOKEN="$jfrog_token"
  echo "JF_OIDC_TOKEN=$jfrog_token" >> "${GITHUB_ENV:-/dev/null}" 2>/dev/null || true
  
  # Set version-specific token environment variable
  if [[ "$version" != "latest" ]]; then
    local version_var="JF_OIDC_TOKEN_${version//[.-]/_}"
    export "$version_var"="$jfrog_token"
    echo "$version_var=$jfrog_token" >> "${GITHUB_ENV:-/dev/null}" 2>/dev/null || true
    log_debug "Version-specific token set: $version_var"
  fi
  
  # Set GitHub Actions output if available
  if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
    echo "enhanced-oidc-token=$jfrog_token" >> "$GITHUB_OUTPUT"
    echo "token-service=$service_name" >> "$GITHUB_OUTPUT"
    echo "token-version=$version" >> "$GITHUB_OUTPUT"
  fi
  
  log_success "Enhanced OIDC token generated successfully for $service_name:$version"
  log_info "Token includes metadata: job_id, run_id, version, branch, workflow, actor"
  
  return 0
}

# Batch token generation for multiple services/versions
generate_batch_tokens() {
  local -a services=("$@")
  local failed_services=()
  
  log_info "Generating enhanced OIDC tokens for ${#services[@]} services"
  
  for service_spec in "${services[@]}"; do
    # Parse service:version format
    local service_name
    local version="latest"
    
    if [[ "$service_spec" == *":"* ]]; then
      service_name="${service_spec%:*}"
      version="${service_spec#*:}"
    else
      service_name="$service_spec"
    fi
    
    if ! generate_enhanced_oidc_token "$service_name" "$version"; then
      failed_services+=("$service_spec")
    fi
  done
  
  if [[ ${#failed_services[@]} -gt 0 ]]; then
    log_error "Failed to generate tokens for: ${failed_services[*]}"
    return 1
  fi
  
  log_success "All enhanced OIDC tokens generated successfully"
  return 0
}

# Cleanup function
cleanup_token_cache() {
  if [[ -d "$OIDC_TOKEN_CACHE_DIR" ]]; then
    log_info "Cleaning up token cache"
    rm -rf "$OIDC_TOKEN_CACHE_DIR"
  fi
}

# Main CLI interface
main() {
  local command="${1:-}"
  
  case "$command" in
    "generate"|"")
      local service_name="${2:-}"
      local version="${3:-latest}"
      
      if [[ -z "$service_name" ]]; then
        log_error "Usage: $0 generate <service_name> [version]"
        log_info "Available services: inventory recommendations checkout web platform helm"
        exit 1
      fi
      
      generate_enhanced_oidc_token "$service_name" "$version"
      ;;
    
    "batch")
      shift
      generate_batch_tokens "$@"
      ;;
    
    "cleanup")
      cleanup_token_cache
      ;;
    
    "list-services")
      log_info "Available services:"
      for service in inventory recommendations checkout web platform helm; do
        echo "  - $service ($(get_service_config "$service"))"
      done
      ;;
    
    "help"|"-h"|"--help")
      cat << EOF
Enhanced OIDC Authentication Script

Usage:
  $0 generate <service_name> [version]     Generate token for a service
  $0 batch <service1[:version1]> ...       Generate tokens for multiple services
  $0 cleanup                               Clean up token cache
  $0 list-services                         List available services
  $0 help                                  Show this help

Examples:
  $0 generate inventory 1.2.3
  $0 batch inventory:1.2.3 web:2.1.0 checkout
  
Environment Variables:
  VERBOSE=true                             Enable debug logging
  PROJECT_KEY=bookverse                    Override project key
  JFROG_URL                               JFrog platform URL (required)
  ACTIONS_ID_TOKEN_REQUEST_URL            GitHub OIDC request URL (required)
  ACTIONS_ID_TOKEN_REQUEST_TOKEN          GitHub OIDC request token (required)

Available Services: inventory recommendations checkout web platform helm
EOF
      ;;
    
    *)
      log_error "Unknown command: $command"
      log_info "Use '$0 help' for usage information"
      exit 1
      ;;
  esac
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
