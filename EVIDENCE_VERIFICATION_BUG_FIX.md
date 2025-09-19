# Evidence Verification Bug Fix

## Issue Summary

**Problem**: Of the evidence published in the checkout service, only 2 that were attached to the application were verified. The rest were not verified due to a configuration bug.

**Root Cause**: The evidence creation commands in the shared evidence library were silently failing due to improper error handling.

## Technical Details

### Bug Location
File: `/Users/yonatanp/playground/AppTrust-BookVerse/bookverse-infra/libraries/bookverse-devops/scripts/evidence-lib.sh`

Lines: 75, 93, and 107

### The Problem
Each `jf evd create-evidence` command ended with `|| true`, which caused:

1. **Silent failures**: Evidence creation errors were suppressed and didn't fail the pipeline
2. **Partial verification**: Only evidence that successfully attached got verified; failed attachments were silently ignored  
3. **No error feedback**: Issues with evidence signing keys, permissions, or configuration were hidden

### Original Code (Problematic)
```bash
jf evd create-evidence \
  --predicate "$predicate_file" \
  "${md_args[@]}" \
  --predicate-type "$predicate_type" \
  --package-name "${PACKAGE_NAME}" \
  --package-version "${PACKAGE_VERSION}" \
  --package-repo-name "$package_repo_name" \
  --project "${PROJECT_KEY}" \
  --provider-id github-actions \
  --key "${EVIDENCE_PRIVATE_KEY:-}" \
  --key-alias "${EVIDENCE_KEY_ALIAS:-${EVIDENCE_KEY_ALIAS_VAR:-}}" || true
```

## Fix Applied

### New Code (Fixed)
```bash
if ! jf evd create-evidence \
  --predicate "$predicate_file" \
  "${md_args[@]}" \
  --predicate-type "$predicate_type" \
  --package-name "${PACKAGE_NAME}" \
  --package-version "${PACKAGE_VERSION}" \
  --package-repo-name "$package_repo_name" \
  --project "${PROJECT_KEY}" \
  --provider-id github-actions \
  --key "${EVIDENCE_PRIVATE_KEY:-}" \
  --key-alias "${EVIDENCE_KEY_ALIAS:-${EVIDENCE_KEY_ALIAS_VAR:-}}"; then
  echo "❌ Failed to attach evidence to package ${PACKAGE_NAME}:${PACKAGE_VERSION} in $package_repo_name" >&2
  echo "🔍 Check EVIDENCE_PRIVATE_KEY and EVIDENCE_KEY_ALIAS configuration" >&2
  return 1
fi
```

### Changes Made

1. **Removed `|| true`**: Evidence creation failures now properly fail the pipeline
2. **Added proper error handling**: Explicit error checking with meaningful error messages
3. **Added diagnostic output**: Clear indication of what failed and what to check
4. **Consistent error handling**: Applied the same fix to all three evidence attachment modes:
   - Package evidence attachment (lines 65-79)
   - Build evidence attachment (lines 88-101) 
   - Release bundle evidence attachment (lines 106-119)

## Impact

### Before Fix
- Evidence creation failures were silently ignored
- Only partially working evidence appeared as "verified"
- No indication of configuration issues
- Difficult to troubleshoot evidence problems

### After Fix
- Evidence creation failures will cause the pipeline to fail with clear error messages
- All evidence must successfully attach for the pipeline to continue
- Clear diagnostic information when evidence creation fails
- Easy identification of configuration issues (EVIDENCE_PRIVATE_KEY, EVIDENCE_KEY_ALIAS)

## Testing Recommendations

1. **Run the checkout CI pipeline** to verify the fix works
2. **Check that all evidence types are now properly verified**
3. **Verify error handling** by temporarily misconfiguring evidence keys
4. **Confirm other services** using the same evidence library benefit from the fix

## Files Modified

- `/Users/yonatanp/playground/AppTrust-BookVerse/bookverse-infra/libraries/bookverse-devops/scripts/evidence-lib.sh`

## Next Steps

1. The fix is applied to the shared evidence library, which affects all services using it
2. Next CI run should show proper evidence verification for all evidence types
3. If evidence creation still fails, the error messages will now clearly indicate the configuration issue to fix
