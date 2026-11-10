# Dev workflow for the Attendance & Auto-Scheduler app.
#   make dev   -> PostgreSQL in Docker (localhost:5432, migrated), then the
#                 FastAPI backend (:8035) AND the Flutter desktop client.
# Ctrl-C stops the backend and the client; PostgreSQL keeps running until
# `make db-stop`.

SHELL := /bin/bash
.DEFAULT_GOAL := help

BACKEND_DIR  := backend
FLUTTER_DIR  := attendance_scheduler_app
BACKEND_PORT := 8035
VENV_PY      := .venv/bin/python

# Desktop device for the current OS (override with: make dev DEVICE=windows)
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
  DEVICE ?= macos
else ifeq ($(UNAME_S),Linux)
  DEVICE ?= linux
else
  DEVICE ?= windows
endif

.PHONY: help dev db db-stop backend frontend install test clean

help:
	@echo "Attendance & Auto-Scheduler — dev targets:"
	@echo "  make dev       Run PostgreSQL (Docker) + backend (:$(BACKEND_PORT)) + Flutter desktop ($(DEVICE))"
	@echo "  make db        Start only PostgreSQL in Docker (localhost:5432) and apply migrations"
	@echo "  make db-stop   Stop the Docker PostgreSQL (its data is kept)"
	@echo "  make backend   Run only the FastAPI backend (:$(BACKEND_PORT))"
	@echo "  make frontend  Run only the Flutter desktop client ($(DEVICE))"
	@echo "  make install   Create backend venv + install deps, flutter pub get"
	@echo "  make test      Run backend tests"
	@echo "  make clean     flutter clean (fixes stale macOS build / entitlements errors)"
	@echo ""
	@echo "Override the Flutter device: make dev DEVICE=windows|macos|linux"

dev:
	@bash scripts/dev.sh $(DEVICE) $(BACKEND_PORT)

db:
	@bash scripts/dev_db.sh

db-stop:
	docker compose -f $(BACKEND_DIR)/docker-compose.yml stop db

backend:
	cd $(BACKEND_DIR) && $(VENV_PY) -m uvicorn app.main:app --reload --port $(BACKEND_PORT)

frontend:
	cd $(FLUTTER_DIR) && flutter run -d $(DEVICE)

install:
	cd $(BACKEND_DIR) && python3 -m venv .venv && $(VENV_PY) -m pip install --upgrade pip && $(VENV_PY) -m pip install -r requirements-dev.txt -c requirements.lock
	cd $(FLUTTER_DIR) && flutter pub get

test:
	cd $(BACKEND_DIR) && $(VENV_PY) -m pytest

clean:
	cd $(FLUTTER_DIR) && flutter clean && flutter pub get
