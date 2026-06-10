# scripts/lib/common.sh
#!/bin/bash
# Common functions for test scripts

set -e

# Colors for output
if [ -t 1 ]; then
    GREEN='\033[0;32m'
    RED='\033[0;31m'
    YELLOW='\033[1;33m'
    NC='\033[0m'
else
    GREEN=''
    RED=''
    YELLOW=''
    NC=''
fi

print_success() {
    echo "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo "${YELLOW}[INFO]${NC} $1"
}

run_tests() {
    local app_name=$1
    local source_path=$2
    local report_suffix=$3
    
    print_info "Running tests for $app_name"
    
    pytest "apps/$app_name/tests/" \
        --cov="$source_path" \
        --cov-report=term \
        --cov-report=term-missing \
        --cov-report=html:"reports/${report_suffix}_html" \
        --cov-report=xml:"reports/${report_suffix}_coverage.xml" \
        -v --tb=short
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_success "$app_name tests passed"
    else
        print_error "$app_name tests failed"
        exit $exit_code
    fi
}

generate_summary() {
    local report_file=$1
    echo ""
    echo "=========================================="
    echo "COVERAGE SUMMARY"
    echo "=========================================="
    
    if [ -f "$report_file" ]; then
        head -20 "$report_file"
    else
        print_error "Report file not found: $report_file"
    fi
}