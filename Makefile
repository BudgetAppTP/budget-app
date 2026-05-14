VENV_DIRS := .venv venv

# Detect existing virtual environment
define detect_venv
$(shell for d in $(VENV_DIRS); do if [ -d "$$d" ]; then echo $$d; exit; fi; done)
endef

VENV_DIR := $(strip $(call detect_venv))

ifeq ($(VENV_DIR),)
    VENV_DIR := .venv
endif

# Normalize paths and executables by OS
ifeq ($(OS),Windows_NT)
    PYTHON := python
    PYTHON_VENV := $(VENV_DIR)/Scripts/python.exe
    PIP_VENV := $(VENV_DIR)/Scripts/pip.exe
else
    PYTHON := python3
    PYTHON_VENV := $(VENV_DIR)/bin/python
    PIP_VENV := $(VENV_DIR)/bin/pip
endif

# Default target
.PHONY: run
run:
	@echo "Running the project..."
	$(PYTHON_VENV) -m app.run

# Create or reuse venv
.PHONY: venv
venv:
	@if [ ! -e "$(PYTHON_VENV)" ]; then \
		echo "Creating virtual environment ($(VENV_DIR))..."; \
		"$(PYTHON)" -m venv "$(VENV_DIR)"; \
		"$(PYTHON_VENV)" -m pip install --upgrade pip; \
	else \
		echo "Using existing virtual environment ($(VENV_DIR))"; \
	fi
	@echo "Installing dependencies..."
	"$(PIP_VENV)" install -r app/requirements.txt

# Run tests
.PHONY: test
test:
	@echo "Running tests..."
	APP_ENV=test "$(PYTHON_VENV)" -m pytest -c tests/pytest.ini

# Docker (development)
.PHONY: docker-build
docker-build:
	@echo "Building Docker images (development compose)..."
	docker compose -f docker-compose.yaml build

.PHONY: docker-up
docker-up:
	@echo "Starting Docker stack (development compose)..."
	docker compose -f docker-compose.yaml up --build

.PHONY: docker-down
docker-down:
	@echo "Stopping Docker stack (development compose)..."
	docker compose -f docker-compose.yaml down

.PHONY: docker-logs
docker-logs:
	@echo "Showing Docker logs (development compose)..."
	docker compose -f docker-compose.yaml logs -f

# Docker (production)
.PHONY: docker-prod-build
docker-prod-build:
	@echo "Pulling Docker images (production infra + services)..."
	docker compose -f docker-compose-prod-infra.yml pull
	docker compose -f docker-compose-prod-services.yml pull

.PHONY: docker-prod-infra-up
docker-prod-infra-up:
	@echo "Starting production infra stack (db + external nginx)..."
	docker compose -f docker-compose-prod-infra.yml up -d --no-build

.PHONY: docker-prod-services-up
docker-prod-services-up:
	@echo "Starting production services stack (backend + frontend)..."
	docker compose -f docker-compose-prod-services.yml up -d --no-build

.PHONY: docker-prod-up
docker-prod-up:
	@echo "Starting full production stack (infra then services)..."
	docker compose -f docker-compose-prod-infra.yml up -d --no-build
	docker compose -f docker-compose-prod-services.yml up -d --no-build

.PHONY: docker-prod-services-down
docker-prod-services-down:
	@echo "Stopping production services stack (backend + frontend)..."
	docker compose -f docker-compose-prod-services.yml down

.PHONY: docker-prod-down
docker-prod-down:
	@echo "Stopping full production stack (services then infra)..."
	docker compose -f docker-compose-prod-services.yml down
	docker compose -f docker-compose-prod-infra.yml down

.PHONY: docker-prod-infra-down
docker-prod-infra-down:
	@echo "Stopping production infra stack (db + external nginx)..."
	docker compose -f docker-compose-prod-infra.yml down

.PHONY: docker-prod-infra-logs
docker-prod-infra-logs:
	@echo "Showing production infra logs (db + external nginx)..."
	docker compose -f docker-compose-prod-infra.yml logs -f

.PHONY: docker-prod-logs
docker-prod-logs:
	@echo "Showing production services logs (backend + frontend)..."
	docker compose -f docker-compose-prod-services.yml logs -f

.PHONY: docker-prod-services-logs
docker-prod-services-logs:
	@echo "Showing production services logs (backend + frontend)..."
	docker compose -f docker-compose-prod-services.yml logs -f

.PHONY: docker-prod-infra-ps
docker-prod-infra-ps:
	@echo "Showing production infra containers..."
	docker compose -f docker-compose-prod-infra.yml ps

.PHONY: docker-prod-services-ps
docker-prod-services-ps:
	@echo "Showing production services containers..."
	docker compose -f docker-compose-prod-services.yml ps

# Clean up virtual environment and __pycache__
.PHONY: clean
clean:
	@echo "Cleaning virtual environment and __pycache__..."
	"$(PYTHON)" -c "import shutil; shutil.rmtree('$(VENV_DIR)', ignore_errors=True)"
	"$(PYTHON)" -c "import shutil, glob; [shutil.rmtree(p, ignore_errors=True) \
			   for p in glob.glob('__pycache__') + glob.glob('*/__pycache__')]"
	@echo "Clean complete."

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  help       Show this help message"
	@echo "  run        Run the project using the virtual environment"
	@echo "  venv       Create virtual environment and install dependencies"
	@echo "  test       Run tests using pytest"
	@echo "  clean      Remove virtual environment and __pycache__ directories"
	@echo "  docker-build      Build Docker images for development compose"
	@echo "  docker-up         Start development Docker stack (with build)"
	@echo "  docker-down       Stop development Docker stack"
	@echo "  docker-logs       Follow development Docker logs"
	@echo "  docker-prod-build Pull production infra + services images"
	@echo "  docker-prod-up    Start full production stack (infra then services)"
	@echo "  docker-prod-down  Stop full production stack (services then infra)"
	@echo "  docker-prod-infra-up       Start production infra stack"
	@echo "  docker-prod-infra-down     Stop production infra stack"
	@echo "  docker-prod-infra-logs     Follow production infra logs"
	@echo "  docker-prod-infra-ps       Show production infra container status"
	@echo "  docker-prod-services-up    Start production services stack"
	@echo "  docker-prod-services-down  Stop production services stack"
	@echo "  docker-prod-services-logs  Follow production services logs"
	@echo "  docker-prod-services-ps    Show production services container status"
	@echo "  docker-prod-logs           Follow production services logs (alias)"
