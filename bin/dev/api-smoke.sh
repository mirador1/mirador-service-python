#!/usr/bin/env bash
# =============================================================================
# bin/dev/api-smoke.sh — quick smoke test of the FastAPI endpoints.
#
# Mirror of the Java side's api-smoke.sh ; adapted for FastAPI's auto-docs
# at /docs (Swagger UI) + /redoc + /openapi.json. No Hurl dependency :
# uses curl directly to keep the script portable.
#
# What it tests :
# - GET /actuator/health         (composite: DB + Redis + Kafka)
# - GET /actuator/health/liveness
# - GET /actuator/health/readiness
# - GET /actuator/info
# - GET /actuator/quality
# - GET /openapi.json            (FastAPI auto-spec)
# - GET /customers               (paginated, expect empty list initially)
# - POST /customers              (create one)
# - GET /customers/{id}          (read it back)
# - GET /customers/recent        (Redis ring buffer)
# - DELETE /customers/{id}       (cleanup)
#
# Exit code : 0 if all checks pass ; 1 on first failure.
# =============================================================================

set -uo pipefail

BASE="${API_BASE:-http://localhost:8080}"
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'
PASS=0
FAIL=0

probe() {
    local desc="$1" method="$2" path="$3" expected_status="$4"
    shift 4
    local actual
    actual=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$BASE$path" "$@" 2>/dev/null || echo "000")
    if [ "$actual" = "$expected_status" ]; then
        printf "  ${GREEN}✓${NC} %-50s %s %s → %s\n" "$desc" "$method" "$path" "$actual"
        PASS=$((PASS + 1))
        return 0
    else
        printf "  ${RED}✗${NC} %-50s %s %s → %s (expected %s)\n" "$desc" "$method" "$path" "$actual" "$expected_status"
        FAIL=$((FAIL + 1))
        return 1
    fi
}

probe_json() {
    local desc="$1" method="$2" path="$3" expected_status="$4" content_type="$5"
    shift 5
    local actual_status actual_ct
    local response_headers
    response_headers=$(curl -s -D - -o /dev/null -X "$method" "$BASE$path" "$@" 2>/dev/null)
    actual_status=$(echo "$response_headers" | head -1 | awk '{print $2}')
    actual_ct=$(echo "$response_headers" | grep -i "^content-type:" | head -1 | awk '{print tolower($2)}' | tr -d '\r;')
    if [ "$actual_status" = "$expected_status" ] && [[ "$actual_ct" == *"$content_type"* ]]; then
        printf "  ${GREEN}✓${NC} %-50s %s %s → %s (%s)\n" "$desc" "$method" "$path" "$actual_status" "$content_type"
        PASS=$((PASS + 1))
    else
        printf "  ${RED}✗${NC} %-50s %s %s → %s ct=%s (expected %s + %s)\n" "$desc" "$method" "$path" "$actual_status" "$actual_ct" "$expected_status" "$content_type"
        FAIL=$((FAIL + 1))
    fi
}

echo "API smoke against $BASE — $(date +%H:%M:%S)"
echo "── Actuator ──"
probe "health composite"     GET  /actuator/health            200
probe "health liveness"      GET  /actuator/health/liveness   200
probe "health readiness"     GET  /actuator/health/readiness  200
probe "info"                 GET  /actuator/info              200
probe "quality"              GET  /actuator/quality           200
probe_json "openapi spec"    GET  /openapi.json               200 application/json

echo "── Customer CRUD ──"
probe "list customers (v1)"  GET  /customers                  200
CREATED=$(curl -s -X POST "$BASE/customers" -H "content-type: application/json" \
    -d '{"name":"smoke-test","email":"smoke@test.local"}' 2>/dev/null)
NEW_ID=$(echo "$CREATED" | /usr/bin/python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)
if [ -n "$NEW_ID" ]; then
    printf "  ${GREEN}✓${NC} %-50s POST /customers → id=%s\n" "create customer" "$NEW_ID"
    PASS=$((PASS + 1))
    probe "read by id"         GET    /customers/$NEW_ID         200
    probe "recent buffer"      GET    /customers/recent          200
    probe "delete"             DELETE /customers/$NEW_ID         204
    probe "404 after delete"   GET    /customers/$NEW_ID         404
else
    printf "  ${RED}✗${NC} %-50s POST /customers FAILED\n" "create customer"
    FAIL=$((FAIL + 1))
fi

echo
if [ "$FAIL" = "0" ]; then
    printf "${GREEN}All %d checks passed.${NC}\n" "$PASS"
    exit 0
else
    printf "${RED}%d failure(s) out of %d.${NC}\n" "$FAIL" "$((PASS + FAIL))"
    exit 1
fi
