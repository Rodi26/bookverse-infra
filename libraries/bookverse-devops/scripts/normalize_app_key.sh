#!/bin/bash

# BookVerse Application Key Normalization Utility
# 
# This script normalizes application keys to prevent double prefix issues
# that commonly occur in GitHub Actions workflows when constructing 
# application identifiers from repository names.
#
# Usage: 
#   source normalize_app_key.sh
#   NORMALIZED_KEY=$(normalize_app_key "$INPUT_KEY")
#
# Example:
#   INPUT: "bookverse-bookverse-inventory"
#   OUTPUT: "bookverse-inventory"

normalize_app_key() {
    local app_key="$1"
    
    # Handle double prefix: bookverse-bookverse-service -> bookverse-service
    if [[ "$app_key" =~ ^bookverse-bookverse-(.+)$ ]]; then
        echo "bookverse-${BASH_REMATCH[1]}"
    else
        echo "$app_key"
    fi
}

# Export the function so it can be used by workflows
export -f normalize_app_key
