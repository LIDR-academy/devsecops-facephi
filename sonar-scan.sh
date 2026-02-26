#!/usr/bin/env bash
# =============================================================================
# sonar-scan.sh — Run a full SonarQube analysis in one command.
#
# Usage:
#   ./sonar-scan.sh              # start server (if needed) + generate coverage + scan
#   ./sonar-scan.sh --skip-tests # skip test/coverage generation (use existing report)
#   ./sonar-scan.sh --stop       # stop and remove SonarQube containers + volumes
#
# Prerequisites:
#   • Docker + Docker Compose
#   • Node.js + npm (for coverage generation)
#   • SONAR_TOKEN set in .env (generate at http://localhost:9000 after first login)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()    { echo -e "${CYAN}[sonar]${NC} $*"; }
success() { echo -e "${GREEN}[sonar]${NC} $*"; }
warn()    { echo -e "${YELLOW}[sonar]${NC} $*"; }
error()   { echo -e "${RED}[sonar]${NC} $*" >&2; }

# ---------------------------------------------------------------------------
# Load .env so variables are available in this shell
# ---------------------------------------------------------------------------
if [[ -f .env ]]; then
    set -o allexport
    # shellcheck disable=SC1091
    source .env
    set +o allexport
fi

# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------
SKIP_TESTS=false
STOP_MODE=false

for arg in "$@"; do
    case "$arg" in
        --skip-tests) SKIP_TESTS=true ;;
        --stop)       STOP_MODE=true  ;;
        *)
            error "Unknown argument: $arg"
            echo "Usage: $0 [--skip-tests] [--stop]"
            exit 1
            ;;
    esac
done

# ---------------------------------------------------------------------------
# --stop: tear down SonarQube stack
# ---------------------------------------------------------------------------
if [[ "$STOP_MODE" == true ]]; then
    info "Stopping SonarQube stack..."
    docker compose --profile sonarqube down
    success "SonarQube stack stopped."
    exit 0
fi

# ---------------------------------------------------------------------------
# Step 1 — Generate backend test coverage (produces backend/coverage/lcov.info)
# ---------------------------------------------------------------------------
if [[ "$SKIP_TESTS" == false ]]; then
    info "Step 1/3 — Generating backend test coverage..."
    (cd backend && npm test -- --coverage --watchAll=false --forceExit)
    success "Coverage report generated at backend/coverage/lcov.info"
else
    warn "Step 1/3 — Skipping test/coverage generation (--skip-tests)"
    if [[ ! -f backend/coverage/lcov.info ]]; then
        warn "backend/coverage/lcov.info not found — coverage data will be missing from the report."
    fi
fi

# ---------------------------------------------------------------------------
# Step 2 — Start SonarQube server (waits for healthy status)
# ---------------------------------------------------------------------------
info "Step 2/3 — Starting SonarQube server (this may take ~2 min on first run)..."
docker compose --profile sonarqube up sonarqube sonar-db --wait -d

SONARQUBE_URL="${SONAR_HOST_URL:-http://localhost:9000}"
success "SonarQube is up → ${SONARQUBE_URL}"

# ---------------------------------------------------------------------------
# Validate SONAR_TOKEN
# ---------------------------------------------------------------------------
if [[ -z "${SONAR_TOKEN:-}" ]]; then
    warn "SONAR_TOKEN is not set in .env"
    warn "On first run:"
    warn "  1. Open ${SONARQUBE_URL} and log in with admin / admin"
    warn "  2. Change the default password when prompted"
    warn "  3. Go to My Account > Security > Generate Token"
    warn "  4. Add SONAR_TOKEN=<your-token> to .env"
    warn "  5. Re-run: ./sonar-scan.sh --skip-tests"
    echo ""
    warn "Proceeding without a token — the scanner may fail with HTTP 401."
fi

# ---------------------------------------------------------------------------
# Step 3 — Run sonar-scanner
# ---------------------------------------------------------------------------
info "Step 3/3 — Running SonarQube scanner..."
docker compose --profile sonarqube run --rm sonar-scanner

echo ""
success "Scan complete!"
success "View results → ${SONARQUBE_URL}/dashboard?id=facephi-secdevops"
