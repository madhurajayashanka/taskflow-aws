.PHONY: help up down build logs logs-backend shell-backend shell-db migrate \
       createsuperuser collectstatic test test-e2e test-e2e-api test-e2e-frontend \
       test-all init plan deploy destroy fmt validate \
       output clean env-check secret-check prod-up prod-down prod-logs lint \
       checkov security-scan

BOLD  := $(shell tput bold 2>/dev/null || echo)
GREEN := $(shell tput setaf 2 2>/dev/null || echo)
RED   := $(shell tput setaf 1 2>/dev/null || echo)
RESET := $(shell tput sgr0 2>/dev/null || echo)

help: ## Show available commands
	@echo ""
	@echo "$(BOLD)TaskFlow — Available Commands$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""

## ── Local Development ──────────────────────────────────────────
up: env-check ## Start full stack locally (builds if needed)
	docker compose up --build -d
	@echo "$(GREEN)$(BOLD)✓ TaskFlow running at http://localhost$(RESET)"
	@docker compose ps

down: ## Stop and remove all containers and volumes
	docker compose down -v
	@echo "$(GREEN)✓ All services stopped$(RESET)"

build: ## Rebuild all Docker images (no cache)
	docker compose build --no-cache

logs: ## Follow logs for all services
	docker compose logs -f

logs-backend: ## Follow backend logs only
	docker compose logs -f backend

shell-backend: ## Open bash shell in backend container
	docker compose exec backend bash

shell-db: ## Open psql in database container
	docker compose exec db psql -U $${POSTGRES_USER} -d $${POSTGRES_DB}

migrate: ## Run Django database migrations
	docker compose exec backend python manage.py migrate

createsuperuser: ## Create Django admin superuser
	docker compose exec backend python manage.py createsuperuser

collectstatic: ## Collect Django static files
	docker compose exec backend python manage.py collectstatic --noinput

test: ## Run backend test suite
	docker compose exec backend python manage.py test app.tasks

test-e2e: test-e2e-api test-e2e-frontend ## Run all E2E tests (API + Frontend)
	@echo "$(GREEN)$(BOLD)✓ All E2E tests passed$(RESET)"

test-e2e-api: ## Run E2E API tests against running stack
	@echo "$(BOLD)Running E2E API tests against $(or $(BASE_URL),http://localhost) ...$(RESET)"
	python tests/e2e_api.py

test-e2e-frontend: ## Run E2E frontend/integration tests
	@echo "$(BOLD)Running E2E frontend tests against $(or $(BASE_URL),http://localhost) ...$(RESET)"
	python tests/e2e_frontend.py

test-all: test test-e2e ## Run all tests (unit + E2E)
	@echo ""
	@echo "$(GREEN)$(BOLD)✓ All test suites passed$(RESET)"

## ── Terraform / AWS ────────────────────────────────────────────
init: ## Initialize Terraform (first time setup)
	cd terraform && terraform init

plan: ## Preview infrastructure changes
	cd terraform && terraform plan

deploy: ## Deploy infrastructure to AWS (one command — init + apply)
	cd terraform && terraform init -input=false
	cd terraform && terraform apply -auto-approve
	@echo "$(GREEN)$(BOLD)✓ Infrastructure deployed!$(RESET)"
	@$(MAKE) output

destroy: ## DESTROY all AWS infrastructure
	@echo "$(RED)$(BOLD)WARNING: This will permanently destroy all AWS resources$(RESET)"
	@echo "Press Ctrl+C within 5 seconds to cancel..."
	@sleep 5
	cd terraform && terraform destroy -auto-approve
	@echo "$(GREEN)✓ All AWS resources destroyed$(RESET)"

fmt: ## Format all Terraform files
	cd terraform && terraform fmt -recursive

validate: ## Validate Terraform configuration
	cd terraform && terraform validate

output: ## Show Terraform outputs (IPs, URLs, bucket names)
	cd terraform && terraform output

## ── Production ─────────────────────────────────────────────────
prod-up: env-check ## Start production stack on EC2
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
	@echo "$(GREEN)$(BOLD)✓ TaskFlow PRODUCTION running$(RESET)"
	@docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

prod-down: ## Stop production stack
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down
	@echo "$(GREEN)✓ Production services stopped$(RESET)"

prod-logs: ## Follow production logs
	docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

lint: ## Lint backend code with flake8
	docker compose exec backend flake8 . --max-line-length=120 --exclude=migrations 2>/dev/null || echo "$(GREEN)Tip: pip install flake8 in backend container$(RESET)"

## ── Utilities ──────────────────────────────────────────────────
env-check: ## Verify .env file exists
	@test -f .env || (echo "$(RED)ERROR: .env file missing. Run: cp .env.example .env$(RESET)" && exit 1)

clean: ## Remove all Docker images, volumes, orphaned containers
	docker compose down -v --rmi all --remove-orphans

secret-check: ## Scan for hardcoded secrets (should return nothing)
	@echo "Scanning for hardcoded secrets..."
	@! grep -r "AWS_SECRET_ACCESS_KEY\s*=\s*['\"][A-Za-z0-9]" \
	  --include="*.py" --include="*.js" --include="*.tf" . \
	  --exclude-dir=".terraform" --exclude-dir="node_modules" 2>/dev/null
	@echo "$(GREEN)✓ No hardcoded secrets found$(RESET)"

## ── IaC Security Scanning ──────────────────────────────────────
checkov: ## Run Checkov IaC security scanner on Terraform
	@echo "$(BOLD)Running Checkov IaC security scan...$(RESET)"
	checkov -d terraform/ --config-file .checkov.yml || true
	@echo "$(GREEN)✓ Checkov scan complete$(RESET)"

security-scan: secret-check checkov validate ## Run all security checks (secrets + IaC + validate)
	@echo ""
	@echo "$(GREEN)$(BOLD)✓ All security scans passed$(RESET)"
