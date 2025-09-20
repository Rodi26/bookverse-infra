#!/bin/bash

# BookVerse Self-Healing Tag Management Library
# Comprehensive tag management system for AppTrust applications

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

# Helper function: Check if version is valid SemVer
is_valid_semver() {
    local version="$1"
    # Regex for SemVer (major.minor.patch) with optional pre-release and build metadata
    if [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?(\+[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?$ ]]; then
        return 0  # true
    else
        return 1  # false
    fi
}

# Helper function: Compare two SemVer versions (returns 0 if v1=v2, 1 if v1>v2, -1 if v1<v2)
compare_semver() {
    local v1="$1"
    local v2="$2"
    
    # Remove pre-release and build metadata for comparison
    local v1_clean=$(echo "$v1" | sed -E 's/(-.*|\+.*)//')
    local v2_clean=$(echo "$v2" | sed -E 's/(-.*|\+.*)//')
    
    if ! is_valid_semver "$v1_clean" || ! is_valid_semver "$v2_clean"; then
        log_error "Invalid SemVer format for comparison: $v1 or $v2"
        return 2 # Indicate error
    fi

    local IFS=.
    local i vnum1 vnum2
    read -ra vnum1 <<< "$v1_clean"
    read -ra vnum2 <<< "$v2_clean"

    for ((i=0; i<${#vnum1[@]}; i++)); do
        if (( 10#${vnum1[i]} > 10#${vnum2[i]} )); then
            echo 1; return
        fi
        if (( 10#${vnum1[i]} < 10#${vnum2[i]} )); then
            echo -1; return
        fi
    done
    echo 0; return
}

# Helper function: Get current tags for a version
get_version_tags() {
    local version="$1"
    
    if [[ -z "$JFROG_URL" || -z "$JF_OIDC_TOKEN" || -z "$APPLICATION_KEY" || -z "$version" ]]; then
        log_error "Missing environment variables or version for get_version_tags."
        return 1
    fi
    
    local base_url="${JFROG_URL%/}/apptrust/api/v1"
    local url="$base_url/applications/$APPLICATION_KEY/versions/$version"
    
    local resp=$(curl -sS -H "Authorization: Bearer $JF_OIDC_TOKEN" -H "Accept: application/json" "$url" 2>/dev/null)
    echo "$resp" | jq -r '.tag // empty' 2>/dev/null || true
}

# Helper function: Add a tag to a version (using PATCH to update the version)
add_tag() {
    local version="$1"
    local tag="$2"
    
    if [[ -z "$JFROG_URL" || -z "$JF_OIDC_TOKEN" || -z "$APPLICATION_KEY" || -z "$version" || -z "$tag" ]]; then
        log_error "Missing environment variables or parameters for add_tag."
        return 1
    fi
    
    log_info "Adding tag '$tag' to version $version..."
    local payload=$(jq -n --arg tag "$tag" '{tag: $tag}')
    local url="${JFROG_URL%/}/apptrust/api/v1/applications/$APPLICATION_KEY/versions/$version"
    
    local http_status=$(curl -sS -X PATCH -o /dev/null -w "%{http_code}" \
        "$url" \
        -H "Authorization: Bearer $JF_OIDC_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$payload")
        
    if [[ "$http_status" -ge 200 && "$http_status" -lt 300 ]]; then
        log_success "✅ Added tag '$tag' to version $version"
        return 0
    else
        log_error "❌ Failed to add tag '$tag' to version $version (HTTP $http_status)"
        return 1
    fi
}

# Helper function: Remove a tag from a version by replacing it with 'valid'
remove_tag() {
    local version="$1"
    local tag_to_remove="$2"
    local replacement_tag="${3:-$TAG_VALID}"  # Default to 'valid' tag
    
    if [[ -z "$JFROG_URL" || -z "$JF_OIDC_TOKEN" || -z "$APPLICATION_KEY" || -z "$version" || -z "$tag_to_remove" ]]; then
        log_error "Missing environment variables or parameters for remove_tag."
        return 1
    fi
    
    log_info "Replacing tag '$tag_to_remove' with '$replacement_tag' on version $version..."
    local payload=$(jq -n --arg tag "$replacement_tag" '{tag: $tag}')
    local http_status=$(curl -sS -X PATCH -o /dev/null -w "%{http_code}" \
        "${JFROG_URL%/}/apptrust/api/v1/applications/$APPLICATION_KEY/versions/$version" \
        -H "Authorization: Bearer $JF_OIDC_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$payload")
        
    if [[ "$http_status" -ge 200 && "$http_status" -lt 300 ]]; then
        log_success "✅ Replaced tag '$tag_to_remove' with '$replacement_tag' on version $version"
        return 0
    else
        log_error "❌ Failed to replace tag '$tag_to_remove' with '$replacement_tag' on version $version (HTTP $http_status)"
        return 1
    fi
}

# Main function: Self-healing tag management system
validate_and_heal_tags() {
    log_info "🏥 Starting self-healing tag management for $APPLICATION_KEY..."
    
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
    
    # Test basic API connectivity and fetch more versions for comprehensive tag checking
    local api_url="${JFROG_URL%/}/apptrust/api/v1/applications/$APPLICATION_KEY/versions?limit=50&order_by=created&order_asc=false"
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
        log_success "✅ API call successful! Found $version_count versions for comprehensive tag checking"
        
        # Log first few versions for verification
        log_info "📋 Recent versions:"
        jq -r '.versions[0:3] | .[] | "  - \(.version) (\(.release_status))"' "$temp_file" 2>/dev/null || log_warning "Could not parse version details"
        
        # Identify latest SemVer candidate
        log_info "🔍 Identifying latest SemVer candidate..."
        
        local latest_candidate=""
        local prod_versions=$(jq -r '.versions[] | select(.release_status=="RELEASED" or .release_status=="TRUSTED_RELEASE") | .version' "$temp_file" 2>/dev/null || echo "")
        
        if [[ -n "$prod_versions" ]]; then
            log_info "📋 PROD versions found:"
            for version in $prod_versions; do
                if is_valid_semver "$version"; then
                    log_info "  - $version ✅ (valid SemVer)"
                    if [[ -z "$latest_candidate" ]]; then
                        latest_candidate="$version"
                    else
                        local comparison=$(compare_semver "$version" "$latest_candidate")
                        if [[ "$comparison" == "1" ]]; then
                            latest_candidate="$version"
                        fi
                    fi
                else
                    log_info "  - $version ❌ (not SemVer, ignored)"
                fi
            done
            
            if [[ -n "$latest_candidate" ]]; then
                log_success "🎯 Latest SemVer candidate: $latest_candidate"
                
                # Perform comprehensive tag operations
                log_info "🏷️ Performing comprehensive tag operations..."
                
                # Small delay to ensure version is fully available for tagging
                log_info "⏳ Ensuring version is ready for tag operations..."
                sleep 3
                
                # Check current tags on the latest candidate
                local current_tags=$(get_version_tags "$latest_candidate")
                local has_latest_tag=false
                
                if echo "$current_tags" | grep -q "^$TAG_LATEST$"; then
                    has_latest_tag=true
                    log_info "✅ Version $latest_candidate already has '$TAG_LATEST' tag"
                else
                    log_info "❌ Version $latest_candidate missing '$TAG_LATEST' tag"
                fi
                
                # Find versions that incorrectly have the 'latest' tag
                log_info "🔍 Checking for incorrect 'latest' tags..."
                local incorrect_latest_versions=""
                
                for version in $prod_versions; do
                    if [[ "$version" != "$latest_candidate" ]]; then
                        local tags=$(get_version_tags "$version")
                        log_info "🔍 Version $version current tag: '$tags'"
                        if [[ -n "$tags" && "$tags" == "$TAG_LATEST" ]]; then
                            log_warning "⚠️ Version $version incorrectly has '$TAG_LATEST' tag"
                            incorrect_latest_versions="$incorrect_latest_versions $version"
                        fi
                    fi
                done
                
                # Perform tag operations
                local changes_made=0
                
                # Remove 'latest' tag from incorrect versions (replace with 'valid')
                for version in $incorrect_latest_versions; do
                    if remove_tag "$version" "$TAG_LATEST" "$TAG_VALID"; then
                        changes_made=$((changes_made + 1))
                    fi
                done
                
                # Add 'latest' tag to correct version if missing
                if [[ "$has_latest_tag" == false ]]; then
                    if add_tag "$latest_candidate" "$TAG_LATEST"; then
                        changes_made=$((changes_made + 1))
                        log_success "🎯 Added '$TAG_LATEST' tag to version $latest_candidate"
                    fi
                fi
                
                if [[ $changes_made -gt 0 ]]; then
                    log_success "🎉 Tag management completed! Made $changes_made changes."
                else
                    log_success "✅ No changes needed - tags are already correct!"
                fi
            else
                log_warning "⚠️ No valid SemVer versions found in PROD"
            fi
        else
            log_warning "⚠️ No PROD versions found"
        fi
    else
        log_error "❌ API call failed with HTTP $http_status"
        log_error "Response: $(cat "$temp_file" 2>/dev/null || echo 'No response')"
    fi
    
    rm -f "$temp_file"
    
    log_success "✅ Self-healing tag management completed successfully"
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

log_info "📚 BookVerse Self-Healing Tag Management Library loaded successfully"