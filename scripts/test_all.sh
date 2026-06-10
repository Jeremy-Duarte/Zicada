# scripts/test_all.sh (actualizado)
#!/bin/bash
# Test script for all apps

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT" || exit 1

mkdir -p reports

echo "=========================================="
echo "Running ALL tests (core + products + orders + users)"
echo "=========================================="
echo ""

export DJANGO_SETTINGS_MODULE=config.settings
export PYTHONPATH="$PROJECT_ROOT"

# Run all tests
pytest apps/ \
    --cov=apps \
    --cov-report=term \
    --cov-report=term-missing \
    --cov-report=html:reports/all_html \
    --cov-report=xml:reports/all_coverage.xml \
    -v --tb=short

PYTEST_EXIT=$?

echo ""
echo "=========================================="
echo "COVERAGE SUMMARY"
echo "=========================================="

coverage report 2>/dev/null | grep -E "apps/|TOTAL" || echo "Run 'coverage report' for details"

echo ""
echo "Reports generated:"
echo "  HTML: reports/all_html/index.html"
echo "  XML:  reports/all_coverage.xml"

if [ $PYTEST_EXIT -eq 0 ]; then
    echo ""
    echo "STATUS: ALL TESTS PASSED"
    exit 0
else
    echo ""
    echo "STATUS: SOME TESTS FAILED"
    exit 1
fi