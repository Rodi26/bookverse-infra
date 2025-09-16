#!/bin/bash
# Evidence Library for BookVerse DevOps
# Provides functions for generating and attaching evidence to packages, builds, and applications

set -euo pipefail

# Get the directory of this script to find templates
# Use relative path to work correctly in GitHub Actions checkout environment
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
EVIDENCE_TEMPLATES_DIR="$(dirname "$SCRIPT_DIR")/evidence/templates"

# Auto-set common environment variables if not already set
# These will be inherited from GitHub Actions environment or set to sensible defaults
export SERVICE_NAME="${SERVICE_NAME:-$(echo ${APPLICATION_KEY:-bookverse-service} | sed 's/bookverse-//')}"
export PROJECT_KEY="${PROJECT_KEY:-bookverse}"
export APPLICATION_KEY="${APPLICATION_KEY:-bookverse-$SERVICE_NAME}"
export BUILD_NAME="${BUILD_NAME:-${APPLICATION_KEY}_CI_build}"
export BUILD_NUMBER="${BUILD_NUMBER:-1}"
export APP_VERSION="${APP_VERSION:-1.0.0}"
export COVERAGE_PERCENT="${COVERAGE_PERCENT:-85.0}"

# Auto-detect common GitHub Actions environment variables
export GITHUB_SHA="${GITHUB_SHA:-unknown}"
export GITHUB_REF_NAME="${GITHUB_REF_NAME:-main}"
export GITHUB_REPOSITORY="${GITHUB_REPOSITORY:-bookverse/service}"

echo "📋 Evidence Library: Auto-configured environment variables"
echo "  SERVICE_NAME: $SERVICE_NAME"
echo "  APPLICATION_KEY: $APPLICATION_KEY"
echo "  PROJECT_KEY: $PROJECT_KEY"
echo "  BUILD_NAME: $BUILD_NAME"
echo "  BUILD_NUMBER: $BUILD_NUMBER"
echo "  APP_VERSION: $APP_VERSION"

# Common evidence functions
emit_json() {
  local out_file="${1:-}"; shift
  local content="$*"
  printf "%b\n" "$content" > "$out_file"
}

evd_create() {
  local predicate_file="${1:-}"; local predicate_type="${2:-}"; local markdown_file="${3:-}"
  local md_args=()
  if [[ -n "$markdown_file" ]]; then md_args+=(--markdown "$markdown_file"); fi
  
  # Three modes: package, build, or release bundle
  if [[ "${ATTACH_TO_PACKAGE:-}" == "true" ]]; then
    # Mode 1: Attach to specific package
    # Build URL args conditionally - only add --url if we have a value
    local url_args=()
    if [[ -n "${JFROG_URL:-${JF_URL:-}}" ]]; then
      url_args+=(--url "${JFROG_URL:-${JF_URL:-}}")
    fi
    
    # Determine repository type based on package name/type
    local package_repo_name
    if [[ "${PACKAGE_NAME:-}" =~ ^(config|resources|recommendation-config|recommendations-config|recommendations-resources)$ ]]; then
      # Generic packages (config, resources) go to generic repository
      package_repo_name="${PROJECT_KEY}-${SERVICE_NAME}-internal-generic-nonprod-local"
    else
      # Docker images go to docker repository  
      package_repo_name="${PROJECT_KEY}-${SERVICE_NAME}-internal-docker-nonprod-local"
    fi
    jf evd create-evidence \
      --predicate "$predicate_file" \
      "${md_args[@]}" \
      --predicate-type "$predicate_type" \
      --package-name "${PACKAGE_NAME}" \
      --package-version "${PACKAGE_VERSION}" \
      --package-repo-name "$package_repo_name" \
      --project "${PROJECT_KEY}" \
      --provider-id github-actions \
      "${url_args[@]}" \
      --key "${EVIDENCE_PRIVATE_KEY:-}" \
      --key-alias "${EVIDENCE_KEY_ALIAS:-${EVIDENCE_KEY_ALIAS_VAR:-}}" || true
  elif [[ "${ATTACH_TO_BUILD:-}" == "true" ]]; then
    # Mode 2: Attach to build info
    # Build URL args conditionally - only add --url if we have a value
    local url_args=()
    if [[ -n "${JFROG_URL:-${JF_URL:-}}" ]]; then
      url_args+=(--url "${JFROG_URL:-${JF_URL:-}}")
    fi
    
    jf evd create-evidence \
      --predicate "$predicate_file" \
      "${md_args[@]}" \
      --predicate-type "$predicate_type" \
      --build-name "${BUILD_NAME}" \
      --build-number "${BUILD_NUMBER}" \
      --project "${PROJECT_KEY}" \
      --provider-id github-actions \
      "${url_args[@]}" \
      --key "${EVIDENCE_PRIVATE_KEY:-}" \
      --key-alias "${EVIDENCE_KEY_ALIAS:-${EVIDENCE_KEY_ALIAS_VAR:-}}" || true
  else
    # Mode 3: Attach to release bundle (for application evidence)
    # Build URL args conditionally - only add --url if we have a value
    local url_args=()
    if [[ -n "${JFROG_URL:-${JF_URL:-}}" ]]; then
      url_args+=(--url "${JFROG_URL:-${JF_URL:-}}")
    fi
    
    jf evd create-evidence \
      --predicate "$predicate_file" \
      "${md_args[@]}" \
      --predicate-type "$predicate_type" \
      --release-bundle "${APPLICATION_KEY}" \
      --release-bundle-version "${APP_VERSION}" \
      --project "${PROJECT_KEY}" \
      --provider-id github-actions \
      "${url_args[@]}" \
      --key "${EVIDENCE_PRIVATE_KEY:-}" \
      --key-alias "${EVIDENCE_KEY_ALIAS:-${EVIDENCE_KEY_ALIAS_VAR:-}}" || true
  fi
}

# Generate random values for demo evidence
generate_random_values() {
  export SCAN_ID=$(cat /proc/sys/kernel/random/uuid)
  export TEST_RUN_ID=$(cat /proc/sys/kernel/random/uuid)
  export COLLECTION_ID=$(cat /proc/sys/kernel/random/uuid)
  export ENGAGEMENT_ID=$(cat /proc/sys/kernel/random/uuid)
  export RELEASE_ID="REL-$((10000 + RANDOM % 90000))"
  export CHANGE_ID="CHG$((3000000 + RANDOM % 1000000))"
  
  # Random findings with some variability
  export HIGH_FINDINGS=$((RANDOM % 3))
  export MEDIUM_FINDINGS=$((2 + RANDOM % 5))
  export LOW_FINDINGS=$((8 + RANDOM % 7))
  export TOTAL_VULNERABILITIES=$((HIGH_FINDINGS + MEDIUM_FINDINGS + LOW_FINDINGS))
  
  # Random test metrics
  export TOTAL_TESTS=$((20 + RANDOM % 30))
  export PASSED_TESTS=$((TOTAL_TESTS - RANDOM % 3))
  export TEST_DURATION=$((30 + RANDOM % 120))
  export TOTAL_ASSERTIONS=$((100 + RANDOM % 31))
  export PASSED_ASSERTIONS=$((TOTAL_ASSERTIONS - RANDOM % 5))
  export COLLECTIONS_EXECUTED=$((3 + RANDOM % 5))
  export COLLECTIONS_PASSED=$COLLECTIONS_EXECUTED
  
  # Random scan metrics
  export URLS_SCANNED=$((50 + RANDOM % 100))
  export SCAN_DURATION=$((300 + RANDOM % 600))
  export FILES_SCANNED=$((25 + RANDOM % 50))
  export POLICIES_EVALUATED=$((15 + RANDOM % 20))
  export COMPLIANCE_SCORE=$((85 + RANDOM % 15))
  
  # Random pentest metrics
  export TESTERS_COUNT=$((2 + RANDOM % 4))
  export REMEDIATION_RATE=$((90 + RANDOM % 10))
  
  # Random Jira metrics
  export TICKET_COUNT=$((5 + RANDOM % 15))
  export RESOLVED_ISSUES=$((TICKET_COUNT - RANDOM % 3))
  export APPROVED_BY="manager-$((RANDOM % 5 + 1))"
  
  # Random SonarQube metrics
  export SONAR_PROJECT_KEY="${SERVICE_NAME:-bookverse-service}"
  export DUPLICATION_PERCENT="$(echo "scale=1; $(( RANDOM % 20 )) / 10" | bc)"
  export CODE_SMELLS=$((RANDOM % 10))
  export BUGS=$((RANDOM % 3))
  export VULNERABILITIES=$((RANDOM % 2))
  
  # Random config bundle metrics
  export FILE_COUNT=$((5 + RANDOM % 15))
  export BUNDLE_TYPE="configuration"
  
  # Random deployment metrics
  # Timestamps
  export NOW_TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  
  export REPLICAS_DESIRED=$((2 + RANDOM % 4))
  export REPLICAS_READY=$REPLICAS_DESIRED
  export REVISION="${GITHUB_SHA:0:8}"
  export DEPLOYED_AT="${NOW_TS}"
  export APPROVED_AT="${NOW_TS}"
}

# Process template with environment variable substitution
process_template() {
  local template_file="$1"
  local output_file="$2"
  
  if [[ ! -f "$template_file" ]]; then
    echo "❌ Template not found: $template_file" >&2
    return 1
  fi
  
  # Use envsubst to substitute environment variables
  envsubst < "$template_file" > "$output_file"
  echo "✅ Generated evidence: $output_file"
}

# Package Evidence Functions
attach_package_pytest_evidence() {
  local package_name="${1:-$PACKAGE_NAME}"
  local package_version="${2:-$PACKAGE_VERSION}"
  
  echo "📊 Generating pytest evidence for package: $package_name"
  generate_random_values
  
  export PACKAGE_NAME="$package_name"
  export PACKAGE_VERSION="$package_version"
  export ATTACH_TO_PACKAGE="true"
  
  local template_file="$EVIDENCE_TEMPLATES_DIR/package/docker/pytest-results.json.template"
  process_template "$template_file" "pytest-results.json"
  
  printf "# PyTest Results\n\nTest results for %s package.\n" "$package_name" > pytest-results.md
  evd_create pytest-results.json "https://pytest.org/evidence/results/v1" pytest-results.md
}

attach_package_sast_evidence() {
  local package_name="${1:-$PACKAGE_NAME}"
  local package_version="${2:-$PACKAGE_VERSION}"
  
  echo "🔒 Generating SAST evidence for package: $package_name"
  generate_random_values
  
  export PACKAGE_NAME="$package_name"
  export PACKAGE_VERSION="$package_version"
  export ATTACH_TO_PACKAGE="true"
  
  local template_file="$EVIDENCE_TEMPLATES_DIR/package/docker/sast-scan.json.template"
  process_template "$template_file" "sast-scan.json"
  
  printf "# SAST Scan\n\nStatic analysis results for %s package.\n" "$package_name" > sast-scan.md
  evd_create sast-scan.json "https://checkmarx.com/evidence/sast/v1.1" sast-scan.md
}

attach_package_config_evidence() {
  local package_name="${1:-$PACKAGE_NAME}"
  local package_version="${2:-$PACKAGE_VERSION}"
  
  echo "📦 Generating config bundle evidence for package: $package_name"
  generate_random_values
  
  export PACKAGE_NAME="$package_name"
  export PACKAGE_VERSION="$package_version"
  export ATTACH_TO_PACKAGE="true"
  
  local template_file="$EVIDENCE_TEMPLATES_DIR/package/generic/config-bundle.json.template"
  process_template "$template_file" "config-bundle.json"
  
  printf "# Config Bundle\n\nConfiguration verification for %s package.\n" "$package_name" > config-bundle.md
  evd_create config-bundle.json "https://in-toto.io/Statement/v0.1" config-bundle.md
}

# Build Evidence Functions
attach_build_fossa_evidence() {
  echo "📋 Generating FOSSA license evidence for build"
  generate_random_values
  
  export ATTACH_TO_BUILD="true"
  export ATTACH_TO_PACKAGE="false"
  
  local template_file="$EVIDENCE_TEMPLATES_DIR/build/fossa-license-scan.json.template"
  process_template "$template_file" "fossa-license-scan.json"
  
  printf "# FOSSA License Scan\n\nLicense compliance scan for build %s.\n" "$BUILD_NAME" > fossa-license-scan.md
  evd_create fossa-license-scan.json "https://fossa.com/evidence/license-scan/v2.1" fossa-license-scan.md
}

attach_build_sonar_evidence() {
  echo "📊 Generating SonarQube evidence for build"
  generate_random_values
  
  export ATTACH_TO_BUILD="true"
  export ATTACH_TO_PACKAGE="false"
  
  local template_file="$EVIDENCE_TEMPLATES_DIR/build/sonar-quality-gate.json.template"
  process_template "$template_file" "sonar-quality-gate.json"
  
  printf "# SonarQube Quality Gate\n\nCode quality analysis for build %s.\n" "$BUILD_NAME" > sonar-quality-gate.md
  evd_create sonar-quality-gate.json "https://sonarsource.com/evidence/quality-gate/v1" sonar-quality-gate.md
}

# Application Evidence Functions
attach_application_slsa_evidence() {
  echo "🔐 Generating SLSA provenance evidence for application"
  generate_random_values
  
  export ATTACH_TO_PACKAGE="false"
  export ATTACH_TO_BUILD="false"
  
  local template_file="$EVIDENCE_TEMPLATES_DIR/application/unassigned/slsa-provenance.json.template"                                                            
  process_template "$template_file" "slsa-provenance.json"
  
  printf "# SLSA Provenance\n\nSupply chain provenance for %s v%s.\n" "$APPLICATION_KEY" "$APP_VERSION" > slsa-provenance.md                                    
  evd_create slsa-provenance.json "https://slsa.dev/provenance/v1" slsa-provenance.md                                                                           
}

attach_application_jira_evidence() {
  echo "📋 Generating Jira release evidence for application"
  generate_random_values
  
  export ATTACH_TO_PACKAGE="false"
  export ATTACH_TO_BUILD="false"
  
  local template_file="$EVIDENCE_TEMPLATES_DIR/application/unassigned/jira-release.json.template"
  process_template "$template_file" "jira-release.json"
  
  printf "# Jira Release\n\nRelease tracking for %s v%s.\n" "$APPLICATION_KEY" "$APP_VERSION" > jira-release.md
  evd_create jira-release.json "https://atlassian.com/evidence/jira/release/v1" jira-release.md
}

attach_application_smoke_evidence() {
  echo "💨 Generating smoke test evidence for DEV stage"
  generate_random_values
  
  export ATTACH_TO_PACKAGE="false"
  export ATTACH_TO_BUILD="false"
  
  local template_file="$EVIDENCE_TEMPLATES_DIR/application/dev/smoke-tests.json.template"
  process_template "$template_file" "smoke-tests.json"
  
  printf "# Smoke Tests\n\nDEV environment smoke tests for %s v%s.\n" "$APPLICATION_KEY" "$APP_VERSION" > smoke-tests.md
  evd_create smoke-tests.json "https://bookverse.com/evidence/smoke-tests/v1" smoke-tests.md
}

attach_application_dast_evidence() {
  echo "🔍 Generating DAST evidence for QA stage"
  generate_random_values
  
  export ATTACH_TO_PACKAGE="false"
  export ATTACH_TO_BUILD="false"
  
  local template_file="$EVIDENCE_TEMPLATES_DIR/application/qa/dast-scan.json.template"
  process_template "$template_file" "dast-scan.json"
  
  printf "# DAST Scan\n\nDynamic security testing for %s v%s in QA.\n" "$APPLICATION_KEY" "$APP_VERSION" > dast-scan.md
  evd_create dast-scan.json "https://invicti.com/evidence/dast/v3" dast-scan.md
}

attach_application_api_evidence() {
  echo "🔌 Generating API test evidence for QA stage"
  generate_random_values
  
  export ATTACH_TO_PACKAGE="false"
  export ATTACH_TO_BUILD="false"
  
  local template_file="$EVIDENCE_TEMPLATES_DIR/application/qa/api-tests.json.template"
  process_template "$template_file" "api-tests.json"
  
  printf "# API Tests\n\nAPI integration tests for %s v%s in QA.\n" "$APPLICATION_KEY" "$APP_VERSION" > api-tests.md
  evd_create api-tests.json "https://postman.com/evidence/collection/v2.2" api-tests.md
}

attach_application_iac_evidence() {
  echo "🏗️ Generating IaC scan evidence for STAGING stage"
  generate_random_values
  
  export ATTACH_TO_PACKAGE="false"
  export ATTACH_TO_BUILD="false"
  
  local template_file="$EVIDENCE_TEMPLATES_DIR/application/staging/iac-scan.json.template"
  process_template "$template_file" "iac-scan.json"
  
  printf "# IaC Scan\n\nInfrastructure security scan for %s v%s in STAGING.\n" "$APPLICATION_KEY" "$APP_VERSION" > iac-scan.md
  evd_create iac-scan.json "https://snyk.io/evidence/iac/v1" iac-scan.md
}

attach_application_pentest_evidence() {
  echo "🛡️ Generating pentest evidence for STAGING stage"
  generate_random_values
  
  export ATTACH_TO_PACKAGE="false"
  export ATTACH_TO_BUILD="false"
  
  local template_file="$EVIDENCE_TEMPLATES_DIR/application/staging/pentest.json.template"
  process_template "$template_file" "pentest.json"
  
  printf "# Penetration Test\n\nSecurity testing for %s v%s in STAGING.\n" "$APPLICATION_KEY" "$APP_VERSION" > pentest.md
  evd_create pentest.json "https://cobalt.io/evidence/pentest/v1" pentest.md
}

attach_application_change_evidence() {
  echo "📋 Generating change approval evidence for STAGING stage"
  generate_random_values
  
  export ATTACH_TO_PACKAGE="false"
  export ATTACH_TO_BUILD="false"
  
  local template_file="$EVIDENCE_TEMPLATES_DIR/application/staging/change-approval.json.template"
  process_template "$template_file" "change-approval.json"
  
  printf "# Change Approval\n\nChange management approval for %s v%s promotion to PROD.\n" "$APPLICATION_KEY" "$APP_VERSION" > change-approval.md
  evd_create change-approval.json "https://servicenow.com/evidence/change-req/v1" change-approval.md
}

attach_application_deployment_evidence() {
  echo "🚀 Generating deployment verification evidence for PROD stage"
  generate_random_values
  
  export ATTACH_TO_PACKAGE="false"
  export ATTACH_TO_BUILD="false"
  
  local template_file="$EVIDENCE_TEMPLATES_DIR/application/prod/deployment-verification.json.template"
  process_template "$template_file" "deployment-verification.json"
  
  printf "# Deployment Verification\n\nProduction deployment verification for %s v%s.\n" "$APPLICATION_KEY" "$APP_VERSION" > deployment-verification.md
  evd_create deployment-verification.json "https://argoproj.github.io/argo-cd/evidence/deployment/v1" deployment-verification.md
}

# High-level evidence attachment functions
attach_docker_package_evidence() {
  local package_name="${1:-$PACKAGE_NAME}"
  local package_version="${2:-$PACKAGE_VERSION}"
  
  echo "🐳 Attaching Docker package evidence for: $package_name"
  attach_package_pytest_evidence "$package_name" "$package_version"
  attach_package_sast_evidence "$package_name" "$package_version"
}

attach_generic_package_evidence() {
  local package_name="${1:-$PACKAGE_NAME}"
  local package_version="${2:-$PACKAGE_VERSION}"
  
  echo "📦 Attaching generic package evidence for: $package_name"
  attach_package_config_evidence "$package_name" "$package_version"
}

attach_build_evidence() {
  echo "🏗️ Attaching build evidence"
  attach_build_fossa_evidence
  attach_build_sonar_evidence
}

attach_application_unassigned_evidence() {
  echo "📋 Attaching UNASSIGNED stage evidence"
  attach_application_slsa_evidence
  attach_application_jira_evidence
}

attach_application_dev_evidence() {
  echo "🧪 Attaching DEV stage evidence"
  attach_application_smoke_evidence
}

attach_application_qa_evidence() {
  echo "🔍 Attaching QA stage evidence"
  attach_application_dast_evidence
  attach_application_api_evidence
}

attach_application_staging_evidence() {
  echo "🏗️ Attaching STAGING stage evidence"
  attach_application_iac_evidence
  attach_application_pentest_evidence
  attach_application_change_evidence
}

attach_application_prod_evidence() {
  echo "🚀 Attaching PROD stage evidence"
  attach_application_deployment_evidence
}

# Main evidence attachment function based on stage
attach_evidence_for_stage() {
  local stage_name="${1:-}"
  case "$stage_name" in
    UNASSIGNED)
      attach_application_unassigned_evidence ;;
    DEV)
      attach_application_dev_evidence ;;
    QA)
      attach_application_qa_evidence ;;
    STAGING)
      attach_application_staging_evidence ;;
    PROD)
      attach_application_prod_evidence ;;
    BUILD)
      attach_build_evidence ;;
    *)
      echo "ℹ️ No evidence rule for stage '$stage_name'" ;;
  esac
}

# Shared setup function for promotion workflows
setup_promotion_environment() {
  # Source promotion library if not already loaded
  if ! command -v advance_one_step &> /dev/null; then
    if [[ -f ".github/scripts/promote_lib.sh" ]]; then
      source .github/scripts/promote_lib.sh
    else
      echo "❌ promote_lib.sh not found" >&2
      return 1
    fi
  fi
  
  echo "✅ Promotion environment configured"
}

echo "✅ BookVerse Evidence Library loaded"
