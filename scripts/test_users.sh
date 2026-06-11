# scripts/test_users.sh
#!/bin/bash
# Test script for apps.users

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT" || exit 1

mkdir -p reports

echo "=========================================="
echo "Testing apps.users"
echo "=========================================="

export DJANGO_SETTINGS_MODULE=config.settings
export PYTHONPATH="$PROJECT_ROOT"

pytest apps/users/tests/ \
    --cov=apps.users \
    --cov-report=term \
    --cov-report=term-missing \
    --cov-report=html:reports/users_html \
    --cov-report=xml:reports/users_coverage.xml \
    -v --tb=short

if [ $? -eq 0 ]; then
    echo "SUCCESS: Users tests completed"
    echo ""
    echo "Reports generated:"
    echo "  HTML: reports/users_html/index.html"
    echo "  XML:  reports/users_coverage.xml"
else
    echo "ERROR: Users tests failed"
    exit 1
fi