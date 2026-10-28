.DEFAULT_GOAL := help
SHELL := /bin/bash

PYTHON ?= python3
NODE ?= node
LUA_COMPILER ?= luac
ISO_PROFILE ?=
ISO_OUTPUT ?= build/iso
ISO_WORK ?= build/iso-work

.PHONY: help check source-check modules-check type-check lint-workflows security-scan test test-cli test-shell iso

help:
	@printf '%s\n' \
	  'check          Run source checks, package module checks, and all non-graphical tests' \
	  'source-check   Parse Python, JavaScript, Lua, and Bash sources' \
	  'modules-check  Validate and assemble both package module trees' \
	  'type-check     Check Python module catalog types' \
	  'lint-workflows Validate GitHub Actions workflow syntax' \
	  'security-scan  Scan repository configuration and source with Trivy' \
	  'test           Run CLI and shell test suites' \
	  'test-cli       Run CLI routing and metadata checks' \
	  'test-shell     Run shell and command behavior checks' \
	  'iso            Build an ISO from an ArchISO profile (set ISO_PROFILE)'

check: source-check modules-check test

source-check:
	$(PYTHON) -m compileall -q src tests scripts
	while IFS= read -r -d '' file; do if rg -q '^\.(pragma|import) ' "$$file"; then continue; fi; $(NODE) --check "$$file" || exit 1; done < <(rg --files src default -g '*.js' -0)
	rg --files default -g '*.lua' -0 | xargs -0 -r -n 1 $(LUA_COMPILER) -p
	rg --files -g '*.sh' -0 | xargs -0 -r -n 1 bash -n

modules-check:
	$(PYTHON) scripts/modules.py validate
	bash tests/shell.d/modules-test.sh

type-check:
	mise exec -- ruff check --select ANN401 scripts/modules.py
	mise exec -- ty check --error all scripts/modules.py

lint-workflows:
	mise exec -- jactionlint .github/workflows/*.yml

security-scan:
	mise exec -- trivy fs --scanners vuln,misconfig,secret --exit-code 1 .

test: test-cli test-shell

test-cli:
	./tests/cli

test-shell:
	./tests/shell

iso:
	@if [[ -z "$(ISO_PROFILE)" ]]; then \
	  printf '%s\n' 'Set ISO_PROFILE to the ArchISO profile directory.' >&2; \
	  exit 2; \
	fi
	@if [[ ! -d "$(ISO_PROFILE)" ]]; then \
	  printf 'ArchISO profile directory does not exist: %s\n' "$(ISO_PROFILE)" >&2; \
	  exit 2; \
	fi
	command -v mkarchiso >/dev/null
	install -d -m 0755 "$(ISO_OUTPUT)" "$(ISO_WORK)"
	mkarchiso -v -w "$(ISO_WORK)" -o "$(ISO_OUTPUT)" "$(ISO_PROFILE)"
