SHELL := /bin/sh
ARCHIVE_DIR ?= ../archive
WORKSPACE := $(CURDIR)
.DEFAULT_GOAL := help

.PHONY: help

help:
	$(MAKE) -C $(ARCHIVE_DIR) WORKSPACE="$(WORKSPACE)" help

%:
	$(MAKE) -C $(ARCHIVE_DIR) WORKSPACE="$(WORKSPACE)" $@
