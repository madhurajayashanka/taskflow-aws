#!/bin/bash
set -e

# ═══════════════════════════════════════════════════════════════════
# TaskFlow — Initial Setup Script
# ═══════════════════════════════════════════════════════════════════
# Run this script once after cloning the repository to set up
# your local development environment.
#
# Usage: ./scripts/setup.sh
# ═══════════════════════════════════════════════════════════════════

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"
echo -e "${BOLD}       TaskFlow — Development Setup                ${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"
echo ""

# ── Check prerequisites ─────────────────────────────────────────
echo -e "${BOLD}Checking prerequisites...${NC}"

check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} $1 found: $(command -v "$1")"
        return 0
    else
        echo -e "  ${RED}✗${NC} $1 not found. Please install it first."
        return 1
    fi
}

MISSING=0
check_command docker || MISSING=1
check_command "docker compose" 2>/dev/null || check_command docker-compose || MISSING=1
check_command make || MISSING=1
check_command git || MISSING=1

if [ "$MISSING" -eq 1 ]; then
    echo ""
    echo -e "${RED}Missing prerequisites. Install them and re-run this script.${NC}"
    exit 1
fi

echo ""

# ── Create .env file ────────────────────────────────────────────
if [ -f .env ]; then
    echo -e "${YELLOW}⚠${NC}  .env file already exists. Skipping..."
else
    echo -e "${BOLD}Creating .env from .env.example...${NC}"
    cp .env.example .env

    # Generate a random SECRET_KEY
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))" 2>/dev/null || openssl rand -base64 50 | tr -d '\n')
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|change-me-to-a-long-random-string|${SECRET_KEY}|" .env
        sed -i '' "s|change-me-to-a-strong-password|$(openssl rand -base64 24 | tr -d '\n')|g" .env
    else
        sed -i "s|change-me-to-a-long-random-string|${SECRET_KEY}|" .env
        sed -i "s|change-me-to-a-strong-password|$(openssl rand -base64 24 | tr -d '\n')|g" .env
    fi

    echo -e "  ${GREEN}✓${NC} .env created with generated secrets"
fi

echo ""

# ── Build and start services ────────────────────────────────────
echo -e "${BOLD}Starting TaskFlow...${NC}"
echo ""

make up

echo ""
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  ✓ TaskFlow is ready!${NC}"
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "  App:        ${BOLD}http://localhost${NC}"
echo -e "  API:        ${BOLD}http://localhost/api/tasks/${NC}"
echo -e "  Health:     ${BOLD}http://localhost/api/health/${NC}"
echo -e "  Admin:      ${BOLD}http://localhost/admin/${NC}"
echo ""
echo -e "  Useful commands:"
echo -e "    make logs           Follow all logs"
echo -e "    make test           Run test suite"
echo -e "    make shell-backend  Open backend shell"
echo -e "    make down           Stop everything"
echo -e "    make help           Show all commands"
echo ""
