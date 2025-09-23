#!/bin/bash

# BookVerse Version Stage Query Utility
#
# This script properly queries version stages using normalized application keys
# to prevent the double prefix issues that cause "unknown" stage results.
#
# Usage:
#   source get_version_stage.sh
#   STAGE=$(get_version_stage "$APP_KEY" "$VERSION" "$JFROG_URL" "$JF_OIDC_TOKEN")

set -euo pipefail

source "$(dirname "$0")/normalize_app_key.sh"

get_version_stage() {
    local app_key="$1"
    local version="$2"
    local jfrog_url="$3"
    local token="$4"
    
    # Normalize the application key to prevent double prefix issues
    local normalized_key
    normalized_key=$(normalize_app_key "$app_key")
    
    if [[ "$app_key" != "$normalized_key" ]]; then
        echo "🔧 [get_version_stage] Normalized: $app_key -> $normalized_key" >&2
    fi
    
    # Query the version content with the normalized key
    local base_url="${jfrog_url%/}/apptrust/api/v1"
    local url="$base_url/applications/$normalized_key/versions/$version/content"
    
    echo "🌐 [get_version_stage] Querying: $url" >&2
    
    local response
    local http_code
    
    response=$(curl -sS -L -w "HTTPSTATUS:%{http_code}" \
        -H "Authorization: Bearer $token" \
        -H "Accept: application/json" \
        "$url" 2>/dev/null || echo "HTTPSTATUS:000")
    
    http_code=$(echo "$response" | sed -n 's/.*HTTPSTATUS:\([0-9]*\)$/\1/p')
    local content=$(echo "$response" | sed 's/HTTPSTATUS:[0-9]*$//')
    
    echo "📡 [get_version_stage] HTTP Status: $http_code" >&2
    
    if [[ "$http_code" -ge 200 && "$http_code" -lt 300 ]]; then
        local stage
        stage=$(echo "$content" | jq -r '.current_stage // empty' 2>/dev/null || echo "")
        echo "$stage"
    else
        echo "❌ [get_version_stage] Failed to get stage for $normalized_key@$version (HTTP $http_code)" >&2
        echo ""
    fi
}

# Export the function so it can be used by workflows
export -f get_version_stage
