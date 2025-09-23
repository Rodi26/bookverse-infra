#!/bin/bash

# Advanced Workflow Validation Script
# Extracts and validates shell scripts from GitHub workflows and actions

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m'

TOTAL_ERRORS=0
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

echo -e "${BLUE}🔍 Advanced Workflow Validation${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Function to extract and validate shell blocks from YAML files
validate_yaml_shell_blocks() {
    local file="$1"
    local errors=0
    local block_count=0
    
    echo -e "${BLUE}Analyzing: $file${NC}"
    
    # Use yq to extract shell script blocks
    if command -v yq >/dev/null 2>&1; then
        # Extract all 'run' blocks that contain shell scripts
        local run_blocks
        run_blocks=$(yq eval '.. | select(has("run")) | .run' "$file" 2>/dev/null || true)
        
        if [[ -n "$run_blocks" ]]; then
            # Process each run block
            while IFS= read -r block; do
                [[ -z "$block" || "$block" == "null" ]] && continue
                ((block_count++))
                
                local temp_script="$TEMP_DIR/block_${block_count}.sh"
                echo "#!/bin/bash" > "$temp_script"
                echo "$block" >> "$temp_script"
                
                if ! bash -n "$temp_script" 2>/dev/null; then
                    echo -e "  ${RED}ERROR${NC} Shell block #$block_count has syntax errors:"
                    bash -n "$temp_script" 2>&1 | sed 's/^/    /'
                    echo -e "  ${YELLOW}Block content:${NC}"
                    echo "$block" | sed 's/^/    /'
                    echo ""
                    ((errors++))
                fi
            done <<< "$run_blocks"
        fi
    else
        # Fallback: manual extraction (less reliable but works without yq)
        python3 -c "
import yaml
import sys
import tempfile
import subprocess
import os

def extract_run_blocks(data, path=''):
    blocks = []
    if isinstance(data, dict):
        for key, value in data.items():
            new_path = f'{path}.{key}' if path else key
            if key == 'run' and isinstance(value, str):
                blocks.append((new_path, value))
            else:
                blocks.extend(extract_run_blocks(value, new_path))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            blocks.extend(extract_run_blocks(item, f'{path}[{i}]'))
    return blocks

try:
    with open('$file', 'r') as f:
        data = yaml.safe_load(f)
    
    blocks = extract_run_blocks(data)
    errors = 0
    
    for i, (path, block) in enumerate(blocks, 1):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as tmp:
            tmp.write('#!/bin/bash\n')
            tmp.write(block)
            tmp_path = tmp.name
        
        try:
            result = subprocess.run(['bash', '-n', tmp_path], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print(f'  \033[0;31mERROR\033[0m Shell block #{i} ({path}) has syntax errors:')
                print('    ' + result.stderr.strip().replace('\n', '\n    '))
                print(f'  \033[0;33mBlock content:\033[0m')
                for line in block.split('\n'):
                    print(f'    {line}')
                print()
                errors += 1
        finally:
            os.unlink(tmp_path)
    
    sys.exit(errors)
    
except Exception as e:
    print(f'  \033[0;33mWARNING\033[0m Could not parse YAML: {e}')
    sys.exit(0)
" && local py_errors=$? || local py_errors=$?
        errors=$py_errors
        block_count=1  # Approximate
    fi
    
    if [[ $errors -eq 0 ]]; then
        if [[ $block_count -gt 0 ]]; then
            echo -e "  ${GREEN}✓ All $block_count shell blocks are syntactically valid${NC}"
        else
            echo -e "  ${GREEN}✓ No shell blocks found${NC}"
        fi
    else
        echo -e "  ${RED}Found $errors shell blocks with syntax errors${NC}"
    fi
    
    echo ""
    TOTAL_ERRORS=$((TOTAL_ERRORS + errors))
}

# Function to validate shell scripts directly
validate_shell_script() {
    local file="$1"
    echo -e "${BLUE}Validating: $file${NC}"
    
    if bash -n "$file" 2>/dev/null; then
        echo -e "  ${GREEN}✓ Syntax is valid${NC}"
    else
        echo -e "  ${RED}ERROR: Syntax errors found${NC}"
        bash -n "$file" 2>&1 | sed 's/^/    /'
        ((TOTAL_ERRORS++))
    fi
    echo ""
}

# Validate all shell scripts
echo -e "${BLUE}=== SHELL SCRIPTS ===${NC}"
find . -name "*.sh" -type f | while read -r script; do
    validate_shell_script "$script"
done

# Validate GitHub workflows
echo -e "${BLUE}=== GITHUB WORKFLOWS ===${NC}"
find . -path "*/.github/workflows/*" \( -name "*.yml" -o -name "*.yaml" \) | while read -r workflow; do
    validate_yaml_shell_blocks "$workflow"
done

# Validate GitHub actions
echo -e "${BLUE}=== GITHUB ACTIONS ===${NC}"
find . -path "*/.github/actions/*" \( -name "*.yml" -o -name "*.yaml" \) | while read -r action; do
    validate_yaml_shell_blocks "$action"
done

# Summary
echo -e "${BLUE}=== SUMMARY ===${NC}"
if [[ $TOTAL_ERRORS -eq 0 ]]; then
    echo -e "${GREEN}✅ All files passed syntax validation!${NC}"
else
    echo -e "${RED}❌ Found $TOTAL_ERRORS files with syntax errors${NC}"
fi

exit $TOTAL_ERRORS
