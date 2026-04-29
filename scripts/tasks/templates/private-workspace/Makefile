SHELL := /bin/sh
ARCHIVE_DIR ?= ../archive
WORKSPACE := $(CURDIR)
.DEFAULT_GOAL := help

.PHONY: help

%:
	$(MAKE) -C $(ARCHIVE_DIR) WORKSPACE="$(WORKSPACE)" $@
