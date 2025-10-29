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
	$(PYTHON_VENV) run.py

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
	"$(PIP_VENV)" install -r requirements.txt

# Run tests
.PHONY: test
test:
	@echo "Running tests..."
	"$(PYTHON_VENV)" -m pytest

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
