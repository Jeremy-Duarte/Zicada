# scripts/coverage_report.sh
#!/bin/bash
# Generate coverage reports from existing .coverage data
# Usage: ./scripts/coverage_report.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT" || exit 1

mkdir -p reports

echo "=========================================="
echo "Generating coverage reports from .coverage"
echo "=========================================="

if [ ! -f .coverage ]; then
    echo "ERROR: .coverage file not found"
    echo "Run tests first: pytest --cov=apps"
    exit 1
fi

echo "Data found in .coverage"

# Generate all report formats
coverage html -d reports/coverage_html
coverage xml -o reports/coverage.xml
coverage json -o reports/coverage.json
coverage report

echo ""
echo "Reports generated:"
echo "  HTML: reports/coverage_html/index.html"
echo "  XML:  reports/coverage.xml"
echo "  JSON: reports/coverage.json"

# Copy to root for SonarQube compatibility
cp reports/coverage.xml coverage.xml 2>/dev/null

echo ""
echo "Coverage summary:"
coverage report | grep TOTAL