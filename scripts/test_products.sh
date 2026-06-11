# scripts/test_products.sh
#!/bin/bash
# Test script for apps.products

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT" || exit 1

mkdir -p reports

echo "=========================================="
echo "Testing apps.products"
echo "=========================================="

export DJANGO_SETTINGS_MODULE=config.settings
export PYTHONPATH="$PROJECT_ROOT"

pytest apps/products/tests/ \
    --cov=apps.products \
    --cov-report=term \
    --cov-report=term-missing \
    --cov-report=html:reports/products_html \
    --cov-report=xml:reports/products_coverage.xml \
    -v --tb=short

if [ $? -eq 0 ]; then
    echo "SUCCESS: Products tests completed"
    echo ""
    echo "Reports generated:"
    echo "  HTML: reports/products_html/index.html"
    echo "  XML:  reports/products_coverage.xml"
else
    echo "ERROR: Products tests failed"
    exit 1
fi