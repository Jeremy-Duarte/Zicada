# scripts/full_coverage.sh
#!/bin/bash
# Complete coverage: run tests + generate all reports
# Usage: ./scripts/full_coverage.sh [core|products|orders|users|all]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT" || exit 1

TARGET="${1:-all}"

mkdir -p reports

echo "=========================================="
echo "FULL COVERAGE REPORT"
echo "Target: $TARGET"
echo "=========================================="

export DJANGO_SETTINGS_MODULE=config.settings
export PYTHONPATH="$PROJECT_ROOT"

case "$TARGET" in
    core)
        pytest apps/core/tests/ --cov=apps.core --cov-report= --cov-append
        ;;
    products)
        pytest apps/products/tests/ --cov=apps.products --cov-append
        ;;
    orders)
        pytest apps/orders/tests/ --cov=apps.orders --cov-append
        ;;
    users)
        pytest apps/users/tests/ --cov=apps.users --cov-append
        ;;
    all)
        pytest apps/ --cov=apps --cov-append
        ;;
    *)
        echo "Invalid target: $TARGET"
        echo "Usage: $0 [core|products|orders|users|all]"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "GENERATING REPORTS"
echo "=========================================="

coverage html -d reports/full_html
coverage xml -o reports/full_coverage.xml
coverage json -o reports/full_coverage.json

# Copy to root for SonarQube
cp reports/full_coverage.xml coverage.xml

echo ""
echo "=========================================="
echo "COVERAGE SUMMARY"
echo "=========================================="
coverage report

echo ""
echo "Reports saved to reports/ directory"
echo "  HTML: reports/full_html/index.html"
echo "  XML:  reports/full_coverage.xml (copied to coverage.xml)"