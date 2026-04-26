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

echo "── E-commerce surface (ADR-0059) — Product/Order/OrderLine ──"
# Re-create a customer for the order FK (we deleted the previous one)
CUST_RESP=$(curl -s -X POST "$BASE/customers" -H "content-type: application/json" \
    -d '{"name":"ecom-test","email":"ecom@test.local"}' 2>/dev/null)
CUST_ID=$(echo "$CUST_RESP" | /usr/bin/python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)

# Create a product
PROD_RESP=$(curl -s -X POST "$BASE/products" -H "content-type: application/json" \
    -d "{\"name\":\"smoke-widget-$$\",\"description\":\"Smoke product\",\"unit_price\":\"10.00\",\"stock_quantity\":100}" 2>/dev/null)
PROD_ID=$(echo "$PROD_RESP" | /usr/bin/python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)

if [ -n "$CUST_ID" ] && [ -n "$PROD_ID" ]; then
    printf "  ${GREEN}✓${NC} %-50s product=%s customer=%s\n" "create product + customer" "$PROD_ID" "$CUST_ID"
    PASS=$((PASS + 1))

    # Create order
    ORD_RESP=$(curl -s -X POST "$BASE/orders" -H "content-type: application/json" \
        -d "{\"customer_id\":$CUST_ID}" 2>/dev/null)
    ORD_ID=$(echo "$ORD_RESP" | /usr/bin/python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)

    if [ -n "$ORD_ID" ]; then
        printf "  ${GREEN}✓${NC} %-50s order=%s\n" "create order" "$ORD_ID"
        PASS=$((PASS + 1))
        # Add 2 lines (qty 2 each → backend snapshots 10.00 → total 40.00)
        curl -s -X POST "$BASE/orders/$ORD_ID/lines" -H "content-type: application/json" \
            -d "{\"product_id\":$PROD_ID,\"quantity\":2}" >/dev/null 2>&1
        curl -s -X POST "$BASE/orders/$ORD_ID/lines" -H "content-type: application/json" \
            -d "{\"product_id\":$PROD_ID,\"quantity\":2}" >/dev/null 2>&1
        # Verify total recomputed
        TOT=$(curl -s "$BASE/orders/$ORD_ID" | /usr/bin/python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('total_amount',''))" 2>/dev/null)
        if [ "$TOT" = "40.00" ]; then
            printf "  ${GREEN}✓${NC} %-50s total=%s\n" "total recomputed (2 lines × 2 × 10.00)" "$TOT"
            PASS=$((PASS + 1))
        else
            printf "  ${RED}✗${NC} %-50s total=%s (expected 40.00)\n" "total recomputed" "$TOT"
            FAIL=$((FAIL + 1))
        fi
        # DELETE order cascades lines
        probe "delete order (cascade lines)" DELETE /orders/$ORD_ID 204
    fi

    # Cleanup product + customer
    probe "delete product"          DELETE /products/$PROD_ID  204
    probe "delete customer"         DELETE /customers/$CUST_ID 204
fi

echo
echo "── MCP server (ADR-0062) — JSON-RPC over /mcp/ ──"
# Mint an admin JWT so we exercise the admin-only path too.
LOGIN_RESP=$(curl -s -X POST "$BASE/auth/login" -H "content-type: application/json" \
    -d '{"username":"admin","password":"admin"}' 2>/dev/null)
TOKEN=$(echo "$LOGIN_RESP" | /usr/bin/python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('access_token',''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    printf "  ${RED}✗${NC} %-50s (no admin user seeded — run alembic + seed first)\n" "mcp: mint JWT"
    FAIL=$((FAIL + 1))
else
    # 1. Initialize the MCP session — accepts JSON-RPC ; SDK assigns a session id.
    INIT_RESP=$(curl -s -i -X POST "$BASE/mcp/" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Accept: application/json, text/event-stream" \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}' 2>/dev/null)
    SESSION_ID=$(echo "$INIT_RESP" | grep -i "^mcp-session-id:" | awk '{print $2}' | tr -d '\r')
    if [ -n "$SESSION_ID" ]; then
        printf "  ${GREEN}✓${NC} %-50s session=%s\n" "mcp: initialize" "${SESSION_ID:0:8}…"
        PASS=$((PASS + 1))
    else
        printf "  ${RED}✗${NC} %-50s\n" "mcp: initialize (no session id)"
        FAIL=$((FAIL + 1))
    fi

    # 2. Send the initialized notification (no response body — ack-only).
    curl -s -X POST "$BASE/mcp/" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Accept: application/json, text/event-stream" \
        -H "Content-Type: application/json" \
        -H "mcp-session-id: $SESSION_ID" \
        -d '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}' >/dev/null 2>&1

    # 3. tools/list — must return 14.
    TOOLS_RESP=$(curl -s -X POST "$BASE/mcp/" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Accept: application/json, text/event-stream" \
        -H "Content-Type: application/json" \
        -H "mcp-session-id: $SESSION_ID" \
        -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' 2>/dev/null)
    TOOL_COUNT=$(echo "$TOOLS_RESP" | /usr/bin/python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('result',{}).get('tools',[])))" 2>/dev/null)
    if [ "$TOOL_COUNT" = "14" ]; then
        printf "  ${GREEN}✓${NC} %-50s count=%s\n" "mcp: tools/list" "$TOOL_COUNT"
        PASS=$((PASS + 1))
    else
        printf "  ${RED}✗${NC} %-50s count=%s (expected 14)\n" "mcp: tools/list" "$TOOL_COUNT"
        FAIL=$((FAIL + 1))
    fi

    # 4. tools/call get_actuator_info — verify the typed JSON shape.
    INFO_RESP=$(curl -s -X POST "$BASE/mcp/" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Accept: application/json, text/event-stream" \
        -H "Content-Type: application/json" \
        -H "mcp-session-id: $SESSION_ID" \
        -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_actuator_info","arguments":{}}}' 2>/dev/null)
    if echo "$INFO_RESP" | grep -q '"title"'; then
        printf "  ${GREEN}✓${NC} %-50s\n" "mcp: tools/call get_actuator_info"
        PASS=$((PASS + 1))
    else
        printf "  ${RED}✗${NC} %-50s\n" "mcp: tools/call get_actuator_info"
        FAIL=$((FAIL + 1))
    fi
fi

echo
if [ "$FAIL" = "0" ]; then
    printf "${GREEN}All %d checks passed.${NC}\n" "$PASS"
    exit 0
else
    printf "${RED}%d failure(s) out of %d.${NC}\n" "$FAIL" "$((PASS + FAIL))"
    exit 1
fi
