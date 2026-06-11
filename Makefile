# Dev workflow for the Attendance & Auto-Scheduler app.
#   make dev   -> runs the FastAPI backend (:8035) AND the Flutter desktop client.
# Ctrl-C stops both (they share a process group).

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

.PHONY: help dev backend frontend install test clean

help:
	@echo "Attendance & Auto-Scheduler — dev targets:"
	@echo "  make dev       Run backend (:$(BACKEND_PORT)) + Flutter desktop ($(DEVICE))"
	@echo "  make backend   Run only the FastAPI backend (:$(BACKEND_PORT))"
	@echo "  make frontend  Run only the Flutter desktop client ($(DEVICE))"
	@echo "  make install   Create backend venv + install deps, flutter pub get"
	@echo "  make test      Run backend tests"
	@echo "  make clean     flutter clean (fixes stale macOS build / entitlements errors)"
	@echo ""
	@echo "Override the Flutter device: make dev DEVICE=windows|macos|linux"

dev:
	@bash scripts/dev.sh $(DEVICE) $(BACKEND_PORT)

backend:
	cd $(BACKEND_DIR) && $(VENV_PY) -m uvicorn app.main:app --reload --port $(BACKEND_PORT)

frontend:
	cd $(FLUTTER_DIR) && flutter run -d $(DEVICE)

install:
	cd $(BACKEND_DIR) && python3 -m venv .venv && $(VENV_PY) -m pip install --upgrade pip && $(VENV_PY) -m pip install -r requirements-dev.txt
	cd $(FLUTTER_DIR) && flutter pub get

test:
	cd $(BACKEND_DIR) && $(VENV_PY) -m pytest

clean:
	cd $(FLUTTER_DIR) && flutter clean && flutter pub get
