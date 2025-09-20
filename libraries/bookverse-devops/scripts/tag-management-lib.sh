#!/bin/bash

# BookVerse Tag Management Library - MINIMAL VERSION
# STEP 1: Complete no-op to establish baseline

set -euo pipefail

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Tag constants
readonly TAG_LATEST="latest"
readonly TAG_QUARANTINE="quarantine"
readonly TAG_VALID="valid"

# Logging functions
log_info() { echo -e "${BLUE}ℹ️  $*${NC}"; }
log_success() { echo -e "${GREEN}✅ $*${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $*${NC}"; }
log_error() { echo -e "${RED}❌ $*${NC}"; }

# Main function: MINIMAL - just validate environment and exit
validate_and_heal_tags() {
    log_info "🏥 Starting MINIMAL tag validation for $APPLICATION_KEY..."
    
    # Validate required environment variables
    if [[ -z "${APPLICATION_KEY:-}" ]]; then
        log_error "APPLICATION_KEY environment variable is required"
        return 1
    fi
    
    if [[ -z "${JFROG_URL:-}" ]]; then
        log_error "JFROG_URL environment variable is required"
        return 1
    fi
    
    if [[ -z "${JF_OIDC_TOKEN:-}" ]]; then
        log_error "JF_OIDC_TOKEN environment variable is required"
        return 1
    fi
    
    # STEP 2: Add simple API call to fetch versions
    log_info "Environment variables validated successfully:"
    log_info "  - APPLICATION_KEY: $APPLICATION_KEY"
    log_info "  - JFROG_URL: $JFROG_URL"
    log_info "  - JF_OIDC_TOKEN: [REDACTED]"
    
    # Test basic API connectivity
    local api_url="${JFROG_URL%/}/apptrust/api/v1/applications/$APPLICATION_KEY/versions?limit=5&order_by=created&order_asc=false"
    log_info "🌐 Testing API call: $api_url"
    
    local temp_file=$(mktemp)
    local http_status
    
    http_status=$(curl -sS -L -o "$temp_file" -w "%{http_code}" \
        "$api_url" \
        -H "Authorization: Bearer $JF_OIDC_TOKEN" \
        -H "Accept: application/json")
    
    log_info "📡 HTTP Status: $http_status"
    
    if [[ "$http_status" -ge 200 && "$http_status" -lt 300 ]]; then
        local version_count=$(jq -r '.versions | length' "$temp_file" 2>/dev/null || echo "0")
        log_success "✅ API call successful! Found $version_count versions"
        
        # Log first few versions for verification
        log_info "📋 Recent versions:"
        jq -r '.versions[0:3] | .[] | "  - \(.version) (\(.release_status))"' "$temp_file" 2>/dev/null || log_warning "Could not parse version details"
    else
        log_error "❌ API call failed with HTTP $http_status"
        log_error "Response: $(cat "$temp_file" 2>/dev/null || echo 'No response')"
    fi
    
    rm -f "$temp_file"
    
    log_success "✅ STEP 2 completed - API connectivity tested"
    return 0
}

# Convenience function for backward compatibility
enforce_latest_tag() {
    local current_version="${1:-$APP_VERSION}"
    
    if [[ -z "$current_version" ]]; then
        log_error "Current version not provided for enforce_latest_tag."
        return 1
    fi
    
    log_info "🏷️ MINIMAL enforce_latest_tag for version $current_version..."
    
    # Run minimal tag validation
    validate_and_heal_tags
    
    log_info "✅ MINIMAL enforcement completed (no actual operations)"
}

# Export functions for use in other scripts
export -f validate_and_heal_tags
export -f enforce_latest_tag

log_info "📚 BookVerse Tag Management Library (MINIMAL) loaded successfully"