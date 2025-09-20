#!/usr/bin/env bash

# Self-Healing Tag Management Library for BookVerse AppTrust
# This library provides comprehensive tag management with self-healing capabilities
#
# Expected environment variables:
# - APPLICATION_KEY: e.g., bookverse-inventory
# - JFROG_URL: base URL to JFrog platform (https://...)
# - PROJECT_KEY: project key (e.g., bookverse)
# - JF_OIDC_TOKEN: OIDC access token (from JFrog token exchange)
#
# Main functions:
# - validate_and_heal_tags: Main entry point for tag validation and healing
# - is_valid_semver: Check if a version follows SemVer rules
# - get_all_versions: Get all versions with their stages and tags
# - calculate_latest_candidate: Find the highest SemVer version in PROD
# - heal_tag_inconsistencies: Fix all tag inconsistencies

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
log_info() {
    echo -e "${BLUE}ℹ️  $*${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $*${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $*${NC}"
}

log_error() {
    echo -e "${RED}❌ $*${NC}"
}

# Validate that a version follows SemVer rules (X.Y.Z with optional pre-release/build metadata)
is_valid_semver() {
    local version="$1"
    
    # SemVer regex: MAJOR.MINOR.PATCH with optional pre-release and build metadata
    # Examples: 1.0.0, 2.1.3-alpha.1, 1.0.0+build.1, 2.0.0-beta.1+exp.sha.5114f85
    local semver_regex='^([0-9]+)\.([0-9]+)\.([0-9]+)(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?(\+[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?$'
    
    if [[ $version =~ $semver_regex ]]; then
        return 0
    else
        return 1
    fi
}

# Compare two SemVer versions (returns 0 if v1 > v2, 1 if v1 < v2, 2 if equal)
compare_semver() {
    local v1="$1"
    local v2="$2"
    
    # Extract major.minor.patch (ignore pre-release and build metadata for comparison)
    local v1_core=$(echo "$v1" | sed -E 's/^([0-9]+\.[0-9]+\.[0-9]+).*/\1/')
    local v2_core=$(echo "$v2" | sed -E 's/^([0-9]+\.[0-9]+\.[0-9]+).*/\1/')
    
    # Use sort -V (version sort) to compare
    if [[ "$v1_core" == "$v2_core" ]]; then
        return 2  # Equal
    elif [[ "$(printf '%s\n%s' "$v1_core" "$v2_core" | sort -V | head -1)" == "$v2_core" ]]; then
        return 0  # v1 > v2
    else
        return 1  # v1 < v2
    fi
}

# Get all versions for the application with their current stage and tags
get_all_versions() {
    local base="${JFROG_URL%/}"
    local temp_file=$(mktemp)
    
    log_info "Fetching all versions for $APPLICATION_KEY..."
    
    # Get versions with pagination to ensure we get all versions
    local all_versions=""
    local offset=0
    local limit=100
    
    while true; do
        local resp=$(curl -sS -H "Authorization: Bearer $JF_OIDC_TOKEN" -H "Accept: application/json" \
            "$base/apptrust/api/v1/applications/$APPLICATION_KEY/versions?limit=$limit&offset=$offset&order_by=created&order_asc=false" || echo '{}')
        
        local versions=$(echo "$resp" | jq -r '.versions[]? | @json' 2>/dev/null || true)
        
        if [[ -z "$versions" ]]; then
            break
        fi
        
        echo "$versions" >> "$temp_file"
        
        local count=$(echo "$versions" | wc -l)
        if [[ $count -lt $limit ]]; then
            break
        fi
        
        offset=$((offset + limit))
    done
    
    echo "$temp_file"
}

# Calculate which version should have the "latest" tag
calculate_latest_candidate() {
    local versions_file="$1"
    local latest_candidate=""
    local latest_version=""
    
    log_info "Calculating latest candidate from PROD versions..."
    
    while IFS= read -r version_json; do
        if [[ -z "$version_json" ]]; then continue; fi
        
        local version=$(echo "$version_json" | jq -r '.version')
        local current_stage=$(echo "$version_json" | jq -r '.current_stage // empty')
        local release_status=$(echo "$version_json" | jq -r '.release_status // empty')
        
        # Only consider versions that are in PROD stage
        if [[ "$current_stage" != "PROD" ]]; then
            continue
        fi
        
        # Only consider released versions
        if [[ "$release_status" != "RELEASED" && "$release_status" != "TRUSTED_RELEASE" ]]; then
            continue
        fi
        
        # Only consider valid SemVer versions
        if ! is_valid_semver "$version"; then
            log_warning "Ignoring non-SemVer version: $version"
            continue
        fi
        
        # Find the highest SemVer version
        if [[ -z "$latest_candidate" ]]; then
            latest_candidate="$version"
            latest_version="$version"
        else
            if compare_semver "$version" "$latest_candidate"; then
                latest_candidate="$version"
                latest_version="$version"
            fi
        fi
        
    done < "$versions_file"
    
    if [[ -n "$latest_candidate" ]]; then
        log_success "Latest candidate: $latest_candidate"
        echo "$latest_candidate"
    else
        log_warning "No valid latest candidate found (no SemVer versions in PROD)"
        echo ""
    fi
}

# Add a tag to a version
add_tag() {
    local version="$1"
    local tag="$2"
    local base="${JFROG_URL%/}"
    
    log_info "Adding tag '$tag' to version $version..."
    
    local resp=$(curl -sS -X POST -H "Authorization: Bearer $JF_OIDC_TOKEN" -H "Content-Type: application/json" \
        -d "{\"tag\": \"$tag\"}" \
        "$base/apptrust/api/v1/applications/$APPLICATION_KEY/versions/$version/tags" || echo '{}')
    
    if echo "$resp" | jq -e '.tag' >/dev/null 2>&1; then
        log_success "Successfully added tag '$tag' to version $version"
        return 0
    else
        log_error "Failed to add tag '$tag' to version $version: $resp"
        return 1
    fi
}

# Remove a tag from a version
remove_tag() {
    local version="$1"
    local tag="$2"
    local base="${JFROG_URL%/}"
    
    log_info "Removing tag '$tag' from version $version..."
    
    local resp=$(curl -sS -X DELETE -H "Authorization: Bearer $JF_OIDC_TOKEN" \
        "$base/apptrust/api/v1/applications/$APPLICATION_KEY/versions/$version/tags/$tag" || echo '{}')
    
    # DELETE operations typically return empty response on success
    log_success "Removed tag '$tag' from version $version"
    return 0
}

# Get current tags for a version
get_version_tags() {
    local version="$1"
    local base="${JFROG_URL%/}"
    
    local resp=$(curl -sS -H "Authorization: Bearer $JF_OIDC_TOKEN" -H "Accept: application/json" \
        "$base/apptrust/api/v1/applications/$APPLICATION_KEY/versions/$version/tags" || echo '{}')
    
    echo "$resp" | jq -r '.tags[]?.tag // empty' 2>/dev/null || true
}

# Determine what tag a version should have based on its state
determine_correct_tag() {
    local version="$1"
    local current_stage="$2"
    local release_status="$3"
    local is_latest_candidate="$4"
    
    # If this is the latest candidate and in PROD, it should have "latest"
    if [[ "$is_latest_candidate" == "true" && "$current_stage" == "PROD" ]]; then
        echo "$TAG_LATEST"
        return
    fi
    
    # If version was rolled back or quarantined
    if [[ "$current_stage" == "QUARANTINE" || "$release_status" == "QUARANTINED" ]]; then
        echo "$TAG_QUARANTINE"
        return
    fi
    
    # If it's a valid SemVer version in any stage (but not latest)
    if is_valid_semver "$version"; then
        echo "$TAG_VALID"
        return
    fi
    
    # For non-SemVer versions, no special tag
    echo ""
}

# Heal tag inconsistencies for all versions
heal_tag_inconsistencies() {
    local versions_file="$1"
    local latest_candidate="$2"
    local changes_made=0
    
    log_info "Healing tag inconsistencies..."
    
    while IFS= read -r version_json; do
        if [[ -z "$version_json" ]]; then continue; fi
        
        local version=$(echo "$version_json" | jq -r '.version')
        local current_stage=$(echo "$version_json" | jq -r '.current_stage // empty')
        local release_status=$(echo "$version_json" | jq -r '.release_status // empty')
        local current_tags=$(echo "$version_json" | jq -r '.tag // empty')
        
        # Determine if this version should be the latest candidate
        local is_latest_candidate="false"
        if [[ "$version" == "$latest_candidate" ]]; then
            is_latest_candidate="true"
        fi
        
        # Determine what tag this version should have
        local correct_tag=$(determine_correct_tag "$version" "$current_stage" "$release_status" "$is_latest_candidate")
        
        # Get actual current tags for this version
        local actual_tags=$(get_version_tags "$version")
        local has_latest=$(echo "$actual_tags" | grep -q "^$TAG_LATEST$" && echo "true" || echo "false")
        local has_quarantine=$(echo "$actual_tags" | grep -q "^$TAG_QUARANTINE$" && echo "true" || echo "false")
        local has_valid=$(echo "$actual_tags" | grep -q "^$TAG_VALID$" && echo "true" || echo "false")
        
        log_info "Version $version: stage=$current_stage, status=$release_status, should_have='$correct_tag'"
        log_info "  Current tags: $(echo "$actual_tags" | tr '\n' ' ' | sed 's/ $//')"
        
        # Remove incorrect tags
        if [[ "$has_latest" == "true" && "$correct_tag" != "$TAG_LATEST" ]]; then
            remove_tag "$version" "$TAG_LATEST"
            changes_made=$((changes_made + 1))
        fi
        
        if [[ "$has_quarantine" == "true" && "$correct_tag" != "$TAG_QUARANTINE" ]]; then
            remove_tag "$version" "$TAG_QUARANTINE"
            changes_made=$((changes_made + 1))
        fi
        
        if [[ "$has_valid" == "true" && "$correct_tag" != "$TAG_VALID" ]]; then
            remove_tag "$version" "$TAG_VALID"
            changes_made=$((changes_made + 1))
        fi
        
        # Add correct tag if missing
        if [[ -n "$correct_tag" ]]; then
            case "$correct_tag" in
                "$TAG_LATEST")
                    if [[ "$has_latest" != "true" ]]; then
                        add_tag "$version" "$TAG_LATEST"
                        changes_made=$((changes_made + 1))
                    fi
                    ;;
                "$TAG_QUARANTINE")
                    if [[ "$has_quarantine" != "true" ]]; then
                        add_tag "$version" "$TAG_QUARANTINE"
                        changes_made=$((changes_made + 1))
                    fi
                    ;;
                "$TAG_VALID")
                    if [[ "$has_valid" != "true" ]]; then
                        add_tag "$version" "$TAG_VALID"
                        changes_made=$((changes_made + 1))
                    fi
                    ;;
            esac
        fi
        
    done < "$versions_file"
    
    return $changes_made
}

# Main function: Validate and heal all tag inconsistencies
validate_and_heal_tags() {
    log_info "🏥 Starting self-healing tag validation for $APPLICATION_KEY..."
    
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
    
    # Get all versions
    local versions_file=$(get_all_versions)
    local version_count=$(wc -l < "$versions_file")
    log_info "Found $version_count versions to analyze"
    
    if [[ $version_count -eq 0 ]]; then
        log_warning "No versions found for $APPLICATION_KEY"
        rm -f "$versions_file"
        return 0
    fi
    
    # Calculate which version should have the "latest" tag
    local latest_candidate=$(calculate_latest_candidate "$versions_file")
    
    # Heal tag inconsistencies
    heal_tag_inconsistencies "$versions_file" "$latest_candidate"
    local changes_made=$?
    
    # Cleanup
    rm -f "$versions_file"
    
    if [[ $changes_made -gt 0 ]]; then
        log_success "🏥 Tag healing completed! Made $changes_made changes."
        log_success "📋 Summary:"
        if [[ -n "$latest_candidate" ]]; then
            log_success "  - Latest version: $latest_candidate (tagged as '$TAG_LATEST')"
        else
            log_warning "  - No latest version (no valid SemVer versions in PROD)"
        fi
        log_success "  - All versions now have correct tags based on their state"
        log_success "  - Non-SemVer versions ignored for 'latest' consideration"
    else
        log_success "🏥 Tag validation completed! No changes needed - all tags are correct."
    fi
    
    return 0
}

# Convenience function for simple latest tag enforcement (backward compatibility)
enforce_latest_tag() {
    local current_version="${1:-$APP_VERSION}"
    
    if [[ -z "$current_version" ]]; then
        log_error "Version not provided and APP_VERSION not set"
        return 1
    fi
    
    log_info "🏷️ Enforcing latest tag for version $current_version..."
    
    # Run full tag validation and healing
    validate_and_heal_tags
    
    # Verify the current version got the latest tag (if it should have it)
    local tags=$(get_version_tags "$current_version")
    if echo "$tags" | grep -q "^$TAG_LATEST$"; then
        log_success "✅ Version $current_version successfully has the 'latest' tag"
    else
        log_warning "⚠️ Version $current_version does not have the 'latest' tag (this may be correct if it's not the highest SemVer version in PROD)"
    fi
}

# Export functions for use in other scripts
export -f validate_and_heal_tags
export -f enforce_latest_tag
export -f is_valid_semver
export -f compare_semver
export -f get_all_versions
export -f calculate_latest_candidate
export -f add_tag
export -f remove_tag
export -f get_version_tags

log_info "📚 BookVerse Tag Management Library loaded successfully"
