.DEFAULT_GOAL := help
SHELL := /bin/bash

PYTHON ?= python3
NODE ?= node
LUA_COMPILER ?= luac
QML_FORMATTER ?= qmlformat
.PHONY: help check source-check modules-check type-check lint-workflows security-scan arch-package-advisories test test-cli test-shell iso

help:
	@printf '%s\n' \
	  'check          Run source checks, package module checks, and all non-graphical tests' \
	  'source-check   Parse Python, JavaScript, Lua, QML, and Bash sources' \
	  'modules-check  Validate and assemble both package module trees' \
	  'type-check     Check strict types across shipped Python sources' \
	  'lint-workflows Validate GitHub Actions workflow syntax' \
	  'security-scan  Scan repository files for secrets with Trivy' \
	  'arch-package-advisories  Review package names against the Arch security tracker' \
	  'test           Run CLI and shell test suites' \
	  'test-cli       Run CLI routing and metadata checks' \
	  'test-shell     Run shell and command behavior checks' \
	  'iso            Build an ISO in the dedicated GitHub Actions release workflow'

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

TYPED_PYTHON_SOURCES := $(shell git ls-files '*.py' ':!:tests/**' | sort)

type-check:
	mise exec -- ruff check --select ANN401 $(TYPED_PYTHON_SOURCES)
	mise exec -- ty check --error all --extra-search-path type-stubs $(TYPED_PYTHON_SOURCES)

lint-workflows:
	mise exec -- jactionlint .github/workflows/*.yml

security-scan:
	mise exec -- trivy fs --scanners secret --exit-code 1 .

arch-package-advisories:
	$(PYTHON) scripts/arch_package_advisories.py

test: test-cli test-shell

test-cli:
	AP="$(CURDIR)" ./tests/cli

test-shell:
	AP="$(CURDIR)" ./tests/shell

iso:
	AP="$(CURDIR)" PATH="$(CURDIR)/src/arch/commands:$$PATH" $(PYTHON) -m scripts.iso.container_build
