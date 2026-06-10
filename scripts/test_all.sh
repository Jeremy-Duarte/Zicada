#!/bin/bash
# scripts/test_all.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT" || exit 1

mkdir -p reports

echo "=========================================="
echo "Running ALL tests with settings_test"
echo "=========================================="

export DJANGO_SETTINGS_MODULE=config.settings_test
export PYTHONPATH="$PROJECT_ROOT"

pytest apps/ \
    --cov=apps \
    --cov-report=term \
    --cov-report=term-missing \
    --cov-report=html:reports/all_html \
    --cov-report=xml:reports/all_coverage.xml \
    -v --tb=short

echo ""
echo "Reports generated:"
echo "  HTML: reports/all_html/index.html"
echo "  XML:  reports/all_coverage.xml"