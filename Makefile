.DEFAULT_GOAL := help
SHELL := /bin/bash

PYTHON ?= python3
NODE ?= node
LUA_COMPILER ?= luac
QML_FORMATTER ?= qmlformat
ARCH_ISO ?= ../arch-iso
ARCH_PKGS ?= ../arch-pkgs

.PHONY: help check source-check modules-check type-check lint-workflows security-scan arch-package-advisories test test-cli test-shell iso

help:
	@printf '%s\n' \
	  'check          Run source checks, package module checks, and all non-graphical tests' \
	  'source-check   Parse Python, JavaScript, Lua, QML, and Bash sources' \
	  'modules-check  Validate and assemble both package module trees' \
	  'type-check     Check Python module catalog types' \
	  'lint-workflows Validate GitHub Actions workflow syntax' \
	  'security-scan  Scan repository files for secrets with Trivy' \
	  'arch-package-advisories  Review package names against the Arch security tracker' \
	  'test           Run CLI and shell test suites' \
	  'test-cli       Run CLI routing and metadata checks' \
	  'test-shell     Run shell and command behavior checks' \
	  'iso            Build an ISO through the companion arch-iso checkout'

check: source-check modules-check test

source-check:
	$(PYTHON) -m compileall -q src tests scripts
	while IFS= read -r -d '' file; do if rg -q '^\.(pragma|import) ' "$$file"; then continue; fi; $(NODE) --check "$$file" || exit 1; done < <(rg --files src default -g '*.js' -0)
	rg --files default -g '*.lua' -0 | xargs -0 -r -n 1 $(LUA_COMPILER) -p
	while IFS= read -r -d '' file; do $(QML_FORMATTER) "$$file" >/dev/null || exit 1; done < <(rg --files src default -g '*.qml' -0)
	rg --files -g '*.sh' -0 | xargs -0 -r -n 1 bash -n

modules-check:
	$(PYTHON) scripts/modules.py validate
	bash tests/shell.d/modules-test.sh

type-check:
	mise exec -- ruff check --select ANN401 scripts/modules.py scripts/arch_package_advisories.py
	mise exec -- ty check --error all scripts/modules.py scripts/arch_package_advisories.py

lint-workflows:
	mise exec -- jactionlint .github/workflows/*.yml

security-scan:
	mise exec -- trivy fs --scanners secret --exit-code 1 .

arch-package-advisories:
	$(PYTHON) scripts/arch_package_advisories.py

test: test-cli test-shell

test-cli:
	ARCH_PATH="$(CURDIR)" ./tests/cli

test-shell:
	ARCH_PATH="$(CURDIR)" ./tests/shell

iso:
	@if [[ ! -x "$(ARCH_ISO)/src/commands/arch-iso-make" ]]; then \
	  printf 'Arch ISO builder not found: %s\n' "$(ARCH_ISO)/src/commands/arch-iso-make" >&2; \
	  exit 2; \
	fi
	@if [[ ! -d "$(ARCH_PKGS)" ]]; then \
	  printf 'Arch package checkout not found: %s\n' "$(ARCH_PKGS)" >&2; \
	  exit 2; \
	fi
	"$(ARCH_ISO)/src/commands/arch-iso-make" --no-boot-offer --local-source "$(CURDIR)" "$(ARCH_PKGS)"
