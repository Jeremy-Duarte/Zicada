# scripts/run.sh (versión final)
#!/bin/bash
# Main runner script
# Usage: ./scripts/run.sh [core|products|orders|users|backoffice|all|coverage|clean|full]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

show_help() {
    echo "Usage: $0 {command}"
    echo ""
    echo "Commands:"
    echo "  core      - Run tests for apps.core"
    echo "  products  - Run tests for apps.products"
    echo "  orders    - Run tests for apps.orders"
    echo "  users     - Run tests for apps.users"
    echo "  backoffice     - Run tests for apps.backoffice"
    echo "  all       - Run all tests"
    echo "  coverage  - Generate reports from existing .coverage"
    echo "  full      - Run all tests + generate full reports"
    echo "  clean     - Remove all coverage reports"
    echo "  quick     - Quick coverage view (no file generation)"
}

case "$1" in
    core|products|orders|users)
        "$SCRIPT_DIR/test_${1}.sh"
        ;;
    all)
        "$SCRIPT_DIR/test_all.sh"
        ;;
    coverage)
        "$SCRIPT_DIR/coverage_report.sh"
        ;;
    full)
        "$SCRIPT_DIR/full_coverage.sh" "${2:-all}"
        ;;
    clean)
        "$SCRIPT_DIR/clean_reports.sh"
        ;;
    quick)
        "$SCRIPT_DIR/coverage_quick.sh"
        ;;
    *)
        show_help
        exit 1
        ;;
esac