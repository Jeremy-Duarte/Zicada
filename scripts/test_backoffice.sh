# scripts/test_backoffice.sh
#!/bin/bash
# Test script for apps.backoffice

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT" || exit 1

# Source common functions
source "$SCRIPT_DIR/lib/common.sh"

mkdir -p reports

print_info "=========================================="
print_info "Testing apps.backoffice"
print_info "=========================================="

export DJANGO_SETTINGS_MODULE=config.settings
export PYTHONPATH="$PROJECT_ROOT"

pytest apps/backoffice/tests/ \
    --cov=apps.backoffice \
    --cov-report=term \
    --cov-report=term-missing \
    --cov-report=html:reports/backoffice_html \
    --cov-report=xml:reports/backoffice_coverage.xml \
    -v --tb=short

if [ $? -eq 0 ]; then
    print_success "Backoffice tests completed"
    echo ""
    echo "Reports generated:"
    echo "  HTML: reports/backoffice_html/index.html"
    echo "  XML:  reports/backoffice_coverage.xml"
else
    print_error "Backoffice tests failed"
    exit 1
fi