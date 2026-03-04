#!/bin/bash
set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "=== TaskFlow Health Check ==="
echo ""

# Check Docker
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker installed"
else
    echo -e "${RED}✗${NC} Docker not found"
    exit 1
fi

# Check running containers
RUNNING=$(docker compose ps --format json 2>/dev/null | grep -c '"running"' || echo "0")
echo -e "  Running containers: ${RUNNING}"

# Check backend health (try HTTPS first, then HTTP for local dev)
BACKEND_STATUS=$(curl -skf https://localhost/api/health/ 2>/dev/null || curl -sf http://localhost/api/health/ 2>/dev/null || echo "unreachable")
if echo "$BACKEND_STATUS" | grep -q '"ok"'; then
    echo -e "${GREEN}✓${NC} Backend API: healthy"
else
    echo -e "${RED}✗${NC} Backend API: ${BACKEND_STATUS}"
fi

# Check frontend
FRONTEND_STATUS=$(curl -skf -o /dev/null -w "%{http_code}" https://localhost/ 2>/dev/null || curl -sf -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✓${NC} Frontend: serving (HTTP ${FRONTEND_STATUS})"
else
    echo -e "${RED}✗${NC} Frontend: HTTP ${FRONTEND_STATUS}"
fi

# Check database via backend health endpoint
if echo "$BACKEND_STATUS" | grep -q '"connected"'; then
    echo -e "${GREEN}✓${NC} Database: connected"
else
    echo -e "${RED}✗${NC} Database: disconnected"
fi

echo ""
echo "=== Check Complete ==="
