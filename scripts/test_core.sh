# scripts/test_core.sh
#!/bin/bash
# Test script for apps.core

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT" || exit 1

# Source common functions
source "$SCRIPT_DIR/lib/common.sh"

mkdir -p reports

print_info "=========================================="
print_info "Testing apps.core"
print_info "=========================================="

export DJANGO_SETTINGS_MODULE=config.settings_test
export PYTHONPATH="$PROJECT_ROOT"

pytest apps/core/tests/ \
    --cov=apps.core \
    --cov-report=term \
    --cov-report=term-missing \
    --cov-report=html:reports/core_html \
    --cov-report=xml:reports/core_coverage.xml \
    -v --tb=short

if [ $? -eq 0 ]; then
    print_success "Core tests completed"
    echo ""
    echo "Reports generated:"
    echo "  HTML: reports/core_html/index.html"
    echo "  XML:  reports/core_coverage.xml"
else
    print_error "Core tests failed"
    exit 1
fi