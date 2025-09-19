#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from typing import List, Optional, Tuple, Dict, Any
import urllib.request
import urllib.parse

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def parse_semver(v: str) -> Optional[Tuple[int, int, int]]:
    m = SEMVER_RE.match(v.strip())
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def bump_patch(v: str) -> str:
    p = parse_semver(v)
    if not p:
        raise ValueError(f"Not a SemVer X.Y.Z: {v}")
    return f"{p[0]}.{p[1]}.{p[2] + 1}"


def max_semver(values: List[str]) -> Optional[str]:
    parsed = [(parse_semver(v), v) for v in values]
    parsed = [(t, raw) for t, raw in parsed if t is not None]
    if not parsed:
        return None
    parsed.sort(key=lambda x: x[0])
    return parsed[-1][1]


def http_get(url: str, headers: Dict[str, str], timeout: int = 30) -> Any:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read().decode("utf-8")
    try:
        return json.loads(data)
    except Exception:
        return data


def http_post(url: str, headers: Dict[str, str], data: str, timeout: int = 30) -> Any:
    """HTTP POST method for AQL queries"""
    req = urllib.request.Request(url, data=data.encode('utf-8'), headers=headers, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        response_data = resp.read().decode("utf-8")
    try:
        return json.loads(response_data)
    except Exception:
        return response_data


def load_version_map(path: str) -> Dict[str, Any]:
    import yaml  # type: ignore
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def find_app_entry(vm: Dict[str, Any], app_key: str) -> Dict[str, Any]:
    for it in vm.get("applications", []) or []:
        if (it.get("key") or "").strip() == app_key:
            return it
    return {}


def compute_next_application_version(app_key: str, vm: Dict[str, Any], jfrog_url: str, token: str) -> str:
    base = jfrog_url.rstrip("/") + "/apptrust/api/v1"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    # Simple version bumping - JFrog artifact uniqueness handled by checksums
    
    # 1) Prefer the most recently created version and bump its patch if SemVer
    latest_url = f"{base}/applications/{urllib.parse.quote(app_key)}/versions?limit=10&order_by=created&order_asc=false"
    try:
        latest_payload = http_get(latest_url, headers)
    except Exception:
        latest_payload = {}

    def first_version(obj: Any) -> Optional[str]:
        if isinstance(obj, dict):
            arr = (
                obj.get("versions")
                or obj.get("results")
                or obj.get("items")
                or obj.get("data")
                or []
            )
            if arr:
                v = (arr[0] or {}).get("version") or (arr[0] or {}).get("name")
                return v if isinstance(v, str) else None
        return None

    latest_created = first_version(latest_payload)
    if isinstance(latest_created, str) and parse_semver(latest_created):
        # Simple patch bump - JFrog handles artifact uniqueness via checksums
        return bump_patch(latest_created)

    # 2) Fallback: scan recent versions and bump the max SemVer present
    url = f"{base}/applications/{urllib.parse.quote(app_key)}/versions?limit=50&order_by=created&order_asc=false"
    try:
        payload = http_get(url, headers)
    except Exception:
        payload = {}

    def extract_versions(obj: Any) -> List[str]:
        if isinstance(obj, dict):
            arr = (
                obj.get("versions")
                or obj.get("results")
                or obj.get("items")
                or obj.get("data")
                or []
            )
            out = []
            for it in arr or []:
                v = (it or {}).get("version") or (it or {}).get("name")
                if isinstance(v, str) and parse_semver(v):
                    out.append(v)
            return out
        elif isinstance(obj, list):
            return [x for x in obj if isinstance(x, str) and parse_semver(x)]
        return []

    values = extract_versions(payload)
    latest = max_semver(values)
    if latest:
        # Simple patch bump - JFrog handles artifact uniqueness via checksums
        return bump_patch(latest)

    # 3) Fallback to seed - IMPORTANT: bump the seed to avoid conflicts with promoted artifacts
    entry = find_app_entry(vm, app_key)
    seed = ((entry.get("seeds") or {}).get("application")) if entry else None
    if not seed or not parse_semver(str(seed)):
        raise SystemExit(f"No valid seed for application {app_key}")
    # Always bump the seed to prevent conflicts with promoted artifacts
    return bump_patch(str(seed))


# BUILD INFO VERSION COMPUTATION REMOVED
# Build info should use GitHub's native build numbers (run_number-run_attempt), 
# not computed semver versions. JFrog build info tracking uses GitHub's format.


def compute_next_package_tag(app_key: str, package_name: str, vm: Dict[str, Any], jfrog_url: str, token: str, project_key: Optional[str]) -> str:
    # Find package configuration and seed
    entry = find_app_entry(vm, app_key)
    pkg = None
    for it in (entry.get("packages") or []):
        if (it.get("name") or "").strip() == package_name:
            pkg = it
            break
    
    if not pkg:
        raise SystemExit(f"Package {package_name} not found in version map for {app_key}")
    
    seed = pkg.get("seed")
    package_type = pkg.get("type", "")
    
    if not seed or not parse_semver(str(seed)):
        raise SystemExit(f"No valid seed for package {app_key}/{package_name}")
    
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    
    # Try to find existing versions to bump from
    existing_versions = []
    
    if package_type == "docker":
        # For Docker packages, query Docker registry API
        try:
            # Extract service name from app_key (bookverse-web -> web)
            service_name = app_key.replace("bookverse-", "")
            # Fix Docker repo pattern to match actual naming convention
            repo_key = f"{project_key or 'bookverse'}-{service_name}-internal-docker-nonprod-local"
            docker_url = f"{jfrog_url.rstrip('/')}/artifactory/api/docker/{repo_key}/v2/{package_name}/tags/list"
            
            resp = http_get(docker_url, headers)
            if isinstance(resp, dict) and "tags" in resp:
                # Filter to valid semver tags only
                for tag in resp.get("tags", []):
                    if isinstance(tag, str) and parse_semver(tag):
                        existing_versions.append(tag)
        except Exception as e:
            # FAIL FAST: Don't mask authentication or connectivity issues
            print(f"ERROR: Docker registry query failed for {package_name}: {e}", file=sys.stderr)
            print(f"ERROR: This indicates authentication or connectivity issues with JFrog", file=sys.stderr)
            print(f"ERROR: Fix authentication before proceeding. Check JFROG_ACCESS_TOKEN.", file=sys.stderr)
            sys.exit(1)
    
    elif package_type == "generic":
        # For generic packages, try to query via AQL to find existing versions
        try:
            # Extract service name from app_key (bookverse-web -> web)
            service_name = app_key.replace("bookverse-", "")
            # Generic repo pattern: bookverse-{service}-internal-generic-nonprod-local
            repo_key = f"{project_key or 'bookverse'}-{service_name}-internal-generic-nonprod-local"
            
            # AQL query to find artifacts in the repository with version patterns
            aql_query = f'''items.find({{"repo":"{repo_key}","type":"file"}}).include("name","path","actual_sha1")'''
            aql_url = f"{jfrog_url.rstrip('/')}/artifactory/api/search/aql"
            aql_headers = headers.copy()
            aql_headers["Content-Type"] = "text/plain"
            
            resp = http_post(aql_url, aql_headers, aql_query)
            print(f"DEBUG: AQL query: {aql_query}", file=sys.stderr)
            print(f"DEBUG: AQL response: {resp}", file=sys.stderr)
            if isinstance(resp, dict) and "results" in resp:
                print(f"DEBUG: Found {len(resp.get('results', []))} items in repository", file=sys.stderr)
                # Extract version numbers from paths/names
                for item in resp.get("results", []):
                    path = item.get("path", "")
                    name = item.get("name", "")
                    
                    # Look for version patterns in path 
                    # Expected path: recommendations/config/1.13.44 or recommendations/resources/5.9.42
                    # Version can be at end of path or followed by slash and filename
                    import re
                    version_pattern = r'/(\d+\.\d+\.\d+)(?:/|$)'
                    match = re.search(version_pattern, path)
                    if match:
                        version = match.group(1)
                        if parse_semver(version):
                            print(f"DEBUG: Found existing version {version} in path: {path}", file=sys.stderr)
                            existing_versions.append(version)
        except Exception as e:
            # FAIL FAST: Don't mask authentication or connectivity issues
            print(f"ERROR: AQL query failed for {package_name}: {e}", file=sys.stderr)
            print(f"ERROR: This indicates authentication or connectivity issues with JFrog", file=sys.stderr)
            print(f"ERROR: AQL URL: {aql_url}", file=sys.stderr)
            print(f"ERROR: Repo: {repo_key}", file=sys.stderr)
            print(f"ERROR: Fix authentication before proceeding. Check JFROG_ACCESS_TOKEN.", file=sys.stderr)
            sys.exit(1)
    
    elif package_type == "helm":
        # For Helm packages, query Helm repository
        try:
            # Extract service name from app_key (bookverse-helm -> helm)
            service_name = app_key.replace("bookverse-", "")
            # Helm repo pattern: bookverse-{service}-internal-helm-nonprod-local
            repo_key = f"{project_key or 'bookverse'}-{service_name}-internal-helm-nonprod-local"
            
            # AQL query to find Helm charts in the repository
            # Note: AQL wildcards use $match instead of shell-style *
            aql_query = f'''items.find({{"repo":"{repo_key}","type":"file","name":{{"$match":"*.tgz"}}}}).include("name","path")'''
            aql_url = f"{jfrog_url.rstrip('/')}/artifactory/api/search/aql"
            aql_headers = headers.copy()
            aql_headers["Content-Type"] = "text/plain"
            
            resp = http_post(aql_url, aql_headers, aql_query)
            print(f"DEBUG: Helm AQL query: {aql_query}", file=sys.stderr)
            print(f"DEBUG: Helm AQL response: {resp}", file=sys.stderr)
            
            # Debug: Also try to see what files exist in the repo at all
            debug_query = f'''items.find({{"repo":"{repo_key}","type":"file"}}).include("name","path").limit(10)'''
            debug_resp = http_post(aql_url, aql_headers, debug_query)
            print(f"DEBUG: All files in helm repo (first 10): {debug_resp}", file=sys.stderr)
            if isinstance(resp, dict) and "results" in resp:
                print(f"DEBUG: Found {len(resp.get('results', []))} Helm charts in repository", file=sys.stderr)
                # Extract version numbers from chart names
                for item in resp.get("results", []):
                    name = item.get("name", "")
                    
                    # Helm chart naming: {chart-name}-{version}.tgz
                    # Extract version from filename like "platform-1.2.3.tgz"
                    import re
                    version_pattern = r'-(\d+\.\d+\.\d+)\.tgz$'
                    match = re.search(version_pattern, name)
                    if match:
                        version = match.group(1)
                        if parse_semver(version):
                            print(f"DEBUG: Found existing Helm version {version} in chart: {name}", file=sys.stderr)
                            existing_versions.append(version)
        except Exception as e:
            # For new repositories that don't exist yet, this is expected - fall back to seed
            error_str = str(e)
            if "400" in error_str or "404" in error_str or "not found" in error_str.lower():
                print(f"INFO: Helm repository {repo_key} not found - this is expected for new packages", file=sys.stderr)
                print(f"INFO: Will fall back to seed version for {package_name}", file=sys.stderr)
                # Don't exit - let it fall through to seed fallback
            else:
                # FAIL FAST: Don't mask real authentication or connectivity issues
                print(f"ERROR: Helm repository query failed for {package_name}: {e}", file=sys.stderr)
                print(f"ERROR: This indicates authentication or connectivity issues with JFrog", file=sys.stderr)
                print(f"ERROR: Helm AQL URL: {aql_url}", file=sys.stderr)
                print(f"ERROR: Helm Repo: {repo_key}", file=sys.stderr)
                print(f"ERROR: Fix authentication before proceeding. Check JFROG_ACCESS_TOKEN.", file=sys.stderr)
                sys.exit(1)
    
    elif package_type == "python" or package_type == "pypi":
        # For Python packages, query PyPI repository
        try:
            # Extract service name from app_key (bookverse-infra -> infra, bookverse-core -> core)
            service_name = app_key.replace("bookverse-", "")
            # PyPI repo pattern: bookverse-{service}-internal-pypi-nonprod-local or bookverse-{service}-internal-python-nonprod-local
            pypi_repo_key = f"{project_key or 'bookverse'}-{service_name}-internal-pypi-nonprod-local"
            python_repo_key = f"{project_key or 'bookverse'}-{service_name}-internal-python-nonprod-local"
            
            # Try both repository naming patterns
            for repo_key in [pypi_repo_key, python_repo_key]:
                print(f"DEBUG: Trying Python repository: {repo_key}", file=sys.stderr)
                
                # AQL query to find Python wheels and source distributions
                # Note: AQL wildcards use $match instead of shell-style *
                aql_query = f'''items.find({{"repo":"{repo_key}","type":"file","name":{{"$match":"*.whl"}}}}).include("name","path")'''
                aql_url = f"{jfrog_url.rstrip('/')}/artifactory/api/search/aql"
                aql_headers = headers.copy()
                aql_headers["Content-Type"] = "text/plain"
                
                resp = http_post(aql_url, aql_headers, aql_query)
                print(f"DEBUG: Python AQL query: {aql_query}", file=sys.stderr)
                print(f"DEBUG: Python AQL response: {resp}", file=sys.stderr)
                
                if isinstance(resp, dict) and "results" in resp and len(resp.get("results", [])) > 0:
                    print(f"DEBUG: Found {len(resp.get('results', []))} Python packages in repository {repo_key}", file=sys.stderr)
                    # Extract version numbers from wheel names
                    for item in resp.get("results", []):
                        name = item.get("name", "")
                        
                        # Python wheel naming: {package-name}-{version}-{python-tag}-{abi-tag}-{platform-tag}.whl
                        # Extract version from filename like "bookverse_core-2.1.8-py3-none-any.whl"
                        import re
                        version_pattern = r'-(\d+\.\d+\.\d+)-'
                        match = re.search(version_pattern, name)
                        if match:
                            version = match.group(1)
                            if parse_semver(version):
                                print(f"DEBUG: Found existing Python version {version} in package: {name}", file=sys.stderr)
                                existing_versions.append(version)
                    break  # Found packages in this repo, stop trying other repos
                else:
                    print(f"DEBUG: No Python packages found in {repo_key}", file=sys.stderr)
                    
        except Exception as e:
            # For new repositories that don't exist yet, this is expected - fall back to seed
            error_str = str(e)
            if "400" in error_str or "404" in error_str or "not found" in error_str.lower():
                print(f"INFO: Python repository not found - this is expected for new packages", file=sys.stderr)
                print(f"INFO: Will fall back to seed version for {package_name}", file=sys.stderr)
                # Don't exit - let it fall through to seed fallback
            else:
                # FAIL FAST: Don't mask real authentication or connectivity issues
                print(f"ERROR: Python repository query failed for {package_name}: {e}", file=sys.stderr)
                print(f"ERROR: This indicates authentication or connectivity issues with JFrog", file=sys.stderr)
                print(f"ERROR: Fix authentication before proceeding. Check JFROG_ACCESS_TOKEN.", file=sys.stderr)
                sys.exit(1)
    
    # If we found existing versions, bump the latest one
    if existing_versions:
        latest = max_semver(existing_versions)
        if latest:
            return bump_patch(latest)
    
    # Fallback to seed - same pattern as application versioning
    print(f"INFO: No existing versions found for {package_name}, falling back to seed version", file=sys.stderr)
    # Always bump the seed to prevent conflicts with promoted artifacts
    return bump_patch(str(seed))


def main():
    p = argparse.ArgumentParser(description="Compute sequential SemVer versions with fallback to seeds")
    p.add_argument("compute", nargs="?")
    p.add_argument("--application-key", required=True)
    p.add_argument("--version-map", required=True)
    p.add_argument("--jfrog-url", required=True)
    p.add_argument("--jfrog-token", required=True)
    p.add_argument("--project-key", required=False)
    p.add_argument("--packages", help="Comma-separated package names to compute tags for", required=False)
    args = p.parse_args()

    vm = load_version_map(args.version_map)
    app_key = args.application_key
    jfrog_url = args.jfrog_url
    token = args.jfrog_token

    app_version = compute_next_application_version(app_key, vm, jfrog_url, token)
    # Build numbers are not computed by semver - they use GitHub's run_number-run_attempt format

    pkg_tags: Dict[str, str] = {}
    if args.packages:
        for name in [x.strip() for x in args.packages.split(",") if x.strip()]:
            pkg_tags[name] = compute_next_package_tag(app_key, name, vm, jfrog_url, token, args.project_key)

    # Export to GITHUB_ENV for the calling workflow
    env_path = os.environ.get("GITHUB_ENV")
    if env_path:
        with open(env_path, "a", encoding="utf-8") as f:
            f.write(f"APP_VERSION={app_version}\n")
            # BUILD_NUMBER is not set by semver - workflows use GitHub's run_number-run_attempt format
            # IMAGE_TAG is set by workflow logic using appropriate package versions
            for k, v in pkg_tags.items():
                key = re.sub(r"[^A-Za-z0-9_]", "_", k.upper())
                f.write(f"DOCKER_TAG_{key}={v}\n")

    # Summary for debugging
    out = {
        "application_key": app_key,
        "app_version": app_version,
        "package_tags": pkg_tags,
        "source": "latest+bump or seed fallback"
    }
    print(json.dumps(out))


if __name__ == "__main__":
    main()
