SHELL := /bin/sh
.DEFAULT_GOAL := help
WORKSPACE ?= .
WORKSPACE_ABS := $(abspath $(WORKSPACE))
ARCHIVE_INSTANCE ?= $(if $(filter $(CURDIR),$(WORKSPACE_ABS)),default,$(notdir $(WORKSPACE_ABS)))
export WORKSPACE ARCHIVE_INSTANCE

.PHONY: help install install-cli install-skill uninstall-skill container-build devshell init-workspace new process-incoming accept-review validate build-content build-linkgraph build-related indexes sidebar dev dev-bg dev-logs dev-status dev-stop build runtime-build runtime-run runtime-logs runtime-status runtime-stop check clean doctor

## Show available commands
help:
	@printf '%s\n' 'Available targets:'
	@awk '\
		/^## / { help = substr($$0, 4); next } \
		/^[a-zA-Z0-9_.-]+:/ { \
			if (help != "") { \
				target = $$1; \
				sub(/:.*/, "", target); \
				printf "  %-16s %s\n", target, help; \
				help = ""; \
			} \
		} \
	' $(MAKEFILE_LIST) | sort

## Build the Podman dev image
install:
	$(MAKE) container-build

## Install the archive CLI into ~/.local/bin
install-cli:
	./scripts/install-cli

## Install the archive-authoring skill into ~/.agents/skills
install-skill:
	./scripts/install-skill

## Remove the archive-authoring skill from ~/.agents/skills
uninstall-skill:
	./scripts/uninstall-skill

## Build the Podman dev image
container-build:
	podman build -t archive-dev:local -f Containerfile.dev .

## Open an interactive shell inside the dev container
devshell:
	./scripts/runtime/devshell

## Initialize a private workspace skeleton at WORKSPACE
init-workspace:
	python3 scripts/tasks/init_workspace.py "$(WORKSPACE)"

## Create a new canonical source entry
new:
	./scripts/runtime/in-container python3 scripts/tasks/new_entry.py --kind "$(kind)" --title "$(title)" $(if $(strip $(section)),--section "$(section)") $(if $(strip $(slug)),--slug "$(slug)") $(if $(strip $(nav_title)),--nav-title "$(nav_title)") $(if $(strip $(summary)),--summary "$(summary)") $(if $(strip $(priority)),--priority "$(priority)") $(if $(strip $(tags)),--tags "$(tags)") $(if $(strip $(related_manual)),--related-manual "$(related_manual)") $(if $(strip $(hide_knowledge_panel)),--hide-knowledge-panel) $(if $(strip $(hide_backlinks)),--hide-backlinks) $(if $(strip $(hide_related)),--hide-related)

## Process incoming files from incoming/new
process-incoming:
	./scripts/runtime/in-container python3 scripts/tasks/process_incoming.py incoming/new

## Accept a reviewed draft into sources
accept-review:
	./scripts/runtime/in-container python3 scripts/tasks/accept_review.py "$(file)"

## Validate all canonical source files
validate:
	./scripts/runtime/in-container python3 scripts/tasks/validate_sources.py

## Build generated content indexes sidebar and nav
build-content:
	./scripts/runtime/in-container bash -lc 'python3 scripts/tasks/build_content.py && python3 scripts/tasks/build_linkgraph.py && python3 scripts/tasks/build_related.py && python3 scripts/tasks/build_indexes.py && python3 scripts/tasks/build_sidebar.py'

## Build generated knowledge page catalog and linkgraph
build-linkgraph:
	./scripts/runtime/in-container python3 scripts/tasks/build_linkgraph.py

## Build generated auto-related suggestions
build-related:
	./scripts/runtime/in-container python3 scripts/tasks/build_related.py

## Build generated index pages only
indexes:
	./scripts/runtime/in-container python3 scripts/tasks/build_indexes.py

## Build generated sidebar only
sidebar:
	./scripts/runtime/in-container python3 scripts/tasks/build_sidebar.py

## Run VitePress dev server after rebuilding content
dev:
	./scripts/runtime/dev

## Start the VitePress dev server in the background
dev-bg:
	./scripts/runtime/dev-bg

## Follow logs for the background VitePress dev server
dev-logs:
	./scripts/runtime/dev-logs

## Show status for the background VitePress dev server
dev-status:
	./scripts/runtime/dev-status

## Stop the background VitePress dev server
dev-stop:
	./scripts/runtime/dev-stop

## Build the static site after rebuilding content
build:
	./scripts/runtime/build

## Package the prebuilt static site into the runtime image
runtime-build:
	./scripts/runtime/runtime-build

## Start the runtime image in the background
runtime-run:
	./scripts/runtime/runtime-run

## Follow logs for the runtime container
runtime-logs:
	./scripts/runtime/runtime-logs

## Show status for the runtime container
runtime-status:
	./scripts/runtime/runtime-status

## Stop the runtime container
runtime-stop:
	./scripts/runtime/runtime-stop

## Run full verification and static build
check:
	./scripts/runtime/in-container bash -lc 'python3 scripts/tasks/validate_sources.py && python3 scripts/tasks/build_content.py && python3 scripts/tasks/build_linkgraph.py && python3 scripts/tasks/build_related.py && python3 scripts/tasks/build_indexes.py && python3 scripts/tasks/build_sidebar.py && npm run docs:build'

## Remove generated output and reports
clean:
	@if [ "$(ARCHIVE_INSTANCE)" = "default" ] && [ "$(WORKSPACE_ABS)" = "$(CURDIR)" ]; then \
		rm -rf content site build/cache build/reports .vitepress/nav.generated.json .vitepress/sidebar.generated.json .vitepress/nav.generated.ts .vitepress/sidebar.generated.ts .vitepress/knowledge; \
	else \
		rm -rf ".instances/$(ARCHIVE_INSTANCE)"; \
	fi

## Check repository health
doctor:
	./scripts/runtime/in-container python3 scripts/tasks/doctor.py
