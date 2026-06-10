# scripts/test_orders.sh
#!/bin/bash
# Test script for apps.orders

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT" || exit 1

mkdir -p reports

echo "=========================================="
echo "Testing apps.orders"
echo "=========================================="

export DJANGO_SETTINGS_MODULE=config.settings
export PYTHONPATH="$PROJECT_ROOT"

pytest apps/orders/tests/ \
    --cov=apps.orders \
    --cov-report=term \
    --cov-report=term-missing \
    --cov-report=html:reports/orders_html \
    --cov-report=xml:reports/orders_coverage.xml \
    -v --tb=short

if [ $? -eq 0 ]; then
    echo "SUCCESS: Orders tests completed"
    echo ""
    echo "Reports generated:"
    echo "  HTML: reports/orders_html/index.html"
    echo "  XML:  reports/orders_coverage.xml"
else
    echo "ERROR: Orders tests failed"
    exit 1
fi