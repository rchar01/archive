#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
REPO_ROOT=$(readlink -f "$SCRIPT_DIR/../..")
CONTAINER_TOOL_ROOT=/workspace
CONTAINER_EXTERNAL_WORKSPACE_ROOT=/workspace-workspace
PODMAN=${PODMAN:-podman}
IMAGE_TAG=${IMAGE_TAG:-archive-dev:local}
CONTAINERFILE=${CONTAINERFILE:-"$REPO_ROOT/Containerfile.dev"}
RUNTIME_CONTAINERFILE=${RUNTIME_CONTAINERFILE:-"$REPO_ROOT/Containerfile.runtime"}
HOST_UID=$(id -u)
HOST_GID=$(id -g)
CONTAINER_HOME=${CONTAINER_HOME:-/tmp/archive-home}
WORKSPACE=${WORKSPACE:-.}
ARCHIVE_INSTANCE_RAW=${ARCHIVE_INSTANCE:-}
ARCHIVE_KNOWLEDGE_GRAPH=${ARCHIVE_KNOWLEDGE_GRAPH:-1}
ARCHIVE_INSTANCE=
INSTANCE_SLUG=
INSTANCE_ROOT=
USE_LEGACY_GENERATED_LAYOUT=0
DEV_CONTAINER_NAME=${DEV_CONTAINER_NAME:-}
RUNTIME_CONTAINER_NAME=${RUNTIME_CONTAINER_NAME:-}
RUNTIME_IMAGE_TAG=${RUNTIME_IMAGE_TAG:-}
BUILD_DIR=${BUILD_DIR:-}
SITE_DIR=${SITE_DIR:-}
RUNTIME_BUILD_CONTEXT_ROOT=${RUNTIME_BUILD_CONTEXT_ROOT:-}
VITEPRESS_DEV_PORT=${VITEPRESS_DEV_PORT:-5173}
RUNTIME_PORT=${RUNTIME_PORT:-8080}
HOST_WORKSPACE=
CONTAINER_WORKSPACE=
WORKSPACE_VOLUME_ARGS=()

normalize_instance_name() {
  local raw=${1:-}
  local cleaned
  cleaned=$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//')
  if [ -z "$cleaned" ]; then
    printf '%s\n' default
    return 0
  fi
  printf '%s\n' "$cleaned"
}

shell_join() {
  local arg
  local joined=""
  for arg in "$@"; do
    joined="$joined$(printf '%q' "$arg") "
  done
  printf '%s' "$joined"
}

resolve_host_workspace() {
  local raw=${1:-.}
  if [ -z "$raw" ]; then
    raw=.
  fi

  if [ "${raw#/}" != "$raw" ]; then
    readlink -m "$raw"
  else
    readlink -m "$(pwd -P)/$raw"
  fi
}

workspace_is_inside_repo() {
  if [ "$HOST_WORKSPACE" = "$REPO_ROOT" ]; then
    return 0
  fi

  case "$HOST_WORKSPACE" in
    "$REPO_ROOT"/*) return 0 ;;
  esac

  return 1
}

resolve_container_workspace() {
  if ! workspace_is_inside_repo; then
    printf '%s\n' "$CONTAINER_EXTERNAL_WORKSPACE_ROOT"
    return 0
  fi

  if [ "$HOST_WORKSPACE" = "$REPO_ROOT" ]; then
    printf '%s\n' "$CONTAINER_TOOL_ROOT"
    return 0
  fi

  printf '%s/%s\n' "$CONTAINER_TOOL_ROOT" "${HOST_WORKSPACE#"$REPO_ROOT"/}"
}

build_workspace_volume_args() {
  WORKSPACE_VOLUME_ARGS=(
    -v "$REPO_ROOT:$CONTAINER_TOOL_ROOT:z"
  )

  if ! workspace_is_inside_repo; then
    WORKSPACE_VOLUME_ARGS+=(
      -v "$HOST_WORKSPACE:$CONTAINER_EXTERNAL_WORKSPACE_ROOT:z"
    )
  fi
}

resolve_workspace_context() {
  HOST_WORKSPACE=$(resolve_host_workspace "$WORKSPACE")
  CONTAINER_WORKSPACE=$(resolve_container_workspace)
  build_workspace_volume_args
}

initialize_instance_context() {
  local default_instance
  if [ -n "$ARCHIVE_INSTANCE_RAW" ]; then
    ARCHIVE_INSTANCE=$(normalize_instance_name "$ARCHIVE_INSTANCE_RAW")
  elif [ "$HOST_WORKSPACE" = "$REPO_ROOT" ]; then
    ARCHIVE_INSTANCE=default
  else
    default_instance=$(basename "$HOST_WORKSPACE")
    ARCHIVE_INSTANCE=$(normalize_instance_name "$default_instance")
  fi

  INSTANCE_SLUG=$ARCHIVE_INSTANCE
  INSTANCE_ROOT="$REPO_ROOT/.instances/$ARCHIVE_INSTANCE"

  if [ "$ARCHIVE_INSTANCE" = default ] && [ "$HOST_WORKSPACE" = "$REPO_ROOT" ]; then
    USE_LEGACY_GENERATED_LAYOUT=1
  else
    USE_LEGACY_GENERATED_LAYOUT=0
  fi

  if [ "$USE_LEGACY_GENERATED_LAYOUT" -eq 1 ]; then
    if [ -z "$DEV_CONTAINER_NAME" ]; then
      DEV_CONTAINER_NAME=archive-dev-server
    fi
    if [ -z "$RUNTIME_CONTAINER_NAME" ]; then
      RUNTIME_CONTAINER_NAME=archive-runtime
    fi
    if [ -z "$RUNTIME_IMAGE_TAG" ]; then
      RUNTIME_IMAGE_TAG=archive-runtime:local
    fi
    if [ -z "$BUILD_DIR" ]; then
      BUILD_DIR="$REPO_ROOT/build"
    fi
    if [ -z "$SITE_DIR" ]; then
      SITE_DIR="$REPO_ROOT/site"
    fi
  else
    if [ -z "$DEV_CONTAINER_NAME" ]; then
      DEV_CONTAINER_NAME="archive-dev-server-$INSTANCE_SLUG"
    fi
    if [ -z "$RUNTIME_CONTAINER_NAME" ]; then
      RUNTIME_CONTAINER_NAME="archive-runtime-$INSTANCE_SLUG"
    fi
    if [ -z "$RUNTIME_IMAGE_TAG" ]; then
      RUNTIME_IMAGE_TAG="archive-runtime:$INSTANCE_SLUG"
    fi
    if [ -z "$BUILD_DIR" ]; then
      BUILD_DIR="$INSTANCE_ROOT/build"
    fi
    if [ -z "$SITE_DIR" ]; then
      SITE_DIR="$INSTANCE_ROOT/site"
    fi
  fi

  if [ -z "$RUNTIME_BUILD_CONTEXT_ROOT" ]; then
    RUNTIME_BUILD_CONTEXT_ROOT="$BUILD_DIR/runtime-image"
  fi
}

resolve_workspace_context
initialize_instance_context

build_image() {
  "$PODMAN" build -t "$IMAGE_TAG" -f "$CONTAINERFILE" "$REPO_ROOT"
}

prepare_runtime_build_context() {
  if [ ! -d "$SITE_DIR" ] || [ ! -f "$SITE_DIR/index.html" ]; then
    printf '%s\n' "Static site output not found at $SITE_DIR; run make build first." >&2
    return 1
  fi

  rm -rf "$RUNTIME_BUILD_CONTEXT_ROOT"
  mkdir -p "$RUNTIME_BUILD_CONTEXT_ROOT/site"
  cp "$RUNTIME_CONTAINERFILE" "$RUNTIME_BUILD_CONTEXT_ROOT/Containerfile.runtime"
  cp "$REPO_ROOT/Caddyfile.runtime" "$RUNTIME_BUILD_CONTEXT_ROOT/Caddyfile.runtime"
  cp -R "$SITE_DIR/." "$RUNTIME_BUILD_CONTEXT_ROOT/site/"
  printf '%s\n' "$RUNTIME_BUILD_CONTEXT_ROOT"
}

build_runtime_image() {
  local context_dir
  context_dir=$(prepare_runtime_build_context)
  "$PODMAN" build -t "$RUNTIME_IMAGE_TAG" -f "$context_dir/Containerfile.runtime" "$context_dir"
}

ensure_workspace_access() {
  local path
  local blocked=0

  for path in .venv-test node_modules content site build; do
    if [ -e "$REPO_ROOT/$path" ] && [ ! -w "$REPO_ROOT/$path" ]; then
      printf '%s\n' "Tool repo path is not writable by uid $HOST_UID: $path" >&2
      blocked=1
    fi
  done

  if [ ! -d "$HOST_WORKSPACE" ]; then
    printf '%s\n' "Workspace root does not exist: $HOST_WORKSPACE" >&2
    blocked=1
  fi

  for path in "$HOST_WORKSPACE" "$HOST_WORKSPACE/incoming" "$HOST_WORKSPACE/sources"; do
    if [ -e "$path" ] && [ ! -w "$path" ]; then
      printf '%s\n' "Workspace path is not writable by uid $HOST_UID: $path" >&2
      blocked=1
    fi
  done

  if [ "$blocked" -ne 0 ]; then
    printf '%s\n' 'Fix ownership before rerunning.' >&2
    return 1
  fi
}

run_container() {
  local command=$1
  ensure_workspace_access
  "$PODMAN" run --rm \
    --userns keep-id \
    --user "$HOST_UID:$HOST_GID" \
    --env HOME="$CONTAINER_HOME" \
    --env WORKSPACE="$CONTAINER_WORKSPACE" \
    --env ARCHIVE_INSTANCE="$ARCHIVE_INSTANCE" \
    --env ARCHIVE_KNOWLEDGE_GRAPH="$ARCHIVE_KNOWLEDGE_GRAPH" \
    "${WORKSPACE_VOLUME_ARGS[@]}" \
    -w "$CONTAINER_TOOL_ROOT" \
    --entrypoint /bin/bash \
    "$IMAGE_TAG" \
    -lc "$command"
}

run_container_with_dev_port() {
  local command=$1
  ensure_workspace_access
  "$PODMAN" run --rm \
    --userns keep-id \
    --user "$HOST_UID:$HOST_GID" \
    --env HOME="$CONTAINER_HOME" \
    --env WORKSPACE="$CONTAINER_WORKSPACE" \
    --env ARCHIVE_INSTANCE="$ARCHIVE_INSTANCE" \
    --env ARCHIVE_KNOWLEDGE_GRAPH="$ARCHIVE_KNOWLEDGE_GRAPH" \
    --env VITEPRESS_DEV_PORT="$VITEPRESS_DEV_PORT" \
    "${WORKSPACE_VOLUME_ARGS[@]}" \
    -w "$CONTAINER_TOOL_ROOT" \
    -p "$VITEPRESS_DEV_PORT:$VITEPRESS_DEV_PORT" \
    --entrypoint /bin/bash \
    "$IMAGE_TAG" \
    -lc "$command"
}

run_container_interactive() {
  ensure_workspace_access
  "$PODMAN" run --rm -it \
    --userns keep-id \
    --user "$HOST_UID:$HOST_GID" \
    --env HOME="$CONTAINER_HOME" \
    --env WORKSPACE="$CONTAINER_WORKSPACE" \
    --env ARCHIVE_INSTANCE="$ARCHIVE_INSTANCE" \
    --env ARCHIVE_KNOWLEDGE_GRAPH="$ARCHIVE_KNOWLEDGE_GRAPH" \
    "${WORKSPACE_VOLUME_ARGS[@]}" \
    -w "$CONTAINER_TOOL_ROOT" \
    -p "$VITEPRESS_DEV_PORT:$VITEPRESS_DEV_PORT" \
    --entrypoint /bin/bash \
    "$IMAGE_TAG" \
    "$@"
}

container_exists() {
  "$PODMAN" container exists "$1"
}

container_running() {
  [ "$("$PODMAN" inspect -f '{{.State.Running}}' "$1" 2>/dev/null || printf 'false')" = "true" ]
}

remove_container_if_exists() {
  local name=$1
  if container_exists "$name"; then
    "$PODMAN" rm -f "$name" >/dev/null
  fi
}

run_container_with_dev_port_background() {
  local name=$1
  local command=$2
  local container_id
  ensure_workspace_access
  remove_container_if_exists "$name"
  container_id=$("$PODMAN" run -d \
    --name "$name" \
    --userns keep-id \
    --user "$HOST_UID:$HOST_GID" \
    --env HOME="$CONTAINER_HOME" \
    --env WORKSPACE="$CONTAINER_WORKSPACE" \
    --env ARCHIVE_INSTANCE="$ARCHIVE_INSTANCE" \
    --env ARCHIVE_KNOWLEDGE_GRAPH="$ARCHIVE_KNOWLEDGE_GRAPH" \
    --env VITEPRESS_DEV_PORT="$VITEPRESS_DEV_PORT" \
    "${WORKSPACE_VOLUME_ARGS[@]}" \
    -w "$CONTAINER_TOOL_ROOT" \
    -p "$VITEPRESS_DEV_PORT:$VITEPRESS_DEV_PORT" \
    --entrypoint /bin/bash \
    "$IMAGE_TAG" \
    -lc "$command")
  sleep 1
  if ! container_running "$name"; then
    printf 'Container failed to stay running: %s\n' "$name" >&2
    "$PODMAN" logs "$name" || true
    return 1
  fi
  printf '%s\n' "$container_id"
}

run_runtime_container_background() {
  local container_id
  remove_container_if_exists "$RUNTIME_CONTAINER_NAME"
  container_id=$("$PODMAN" run -d \
    --name "$RUNTIME_CONTAINER_NAME" \
    -p "$RUNTIME_PORT:80" \
    "$RUNTIME_IMAGE_TAG")
  sleep 1
  if ! container_running "$RUNTIME_CONTAINER_NAME"; then
    printf 'Container failed to stay running: %s\n' "$RUNTIME_CONTAINER_NAME" >&2
    "$PODMAN" logs "$RUNTIME_CONTAINER_NAME" || true
    return 1
  fi
  printf '%s\n' "$container_id"
}

show_container_logs() {
  local name=$1
  if ! container_exists "$name"; then
    printf 'Container not found: %s\n' "$name"
    return 0
  fi
  "$PODMAN" logs -f "$name"
}

show_container_status() {
  local name=$1
  if ! container_exists "$name"; then
    printf 'Container not found: %s\n' "$name"
    return 0
  fi
  "$PODMAN" ps -a --filter "name=^${name}$" --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
}

stop_container() {
  local name=$1
  if ! container_exists "$name"; then
    printf 'Container not found: %s\n' "$name"
    return 0
  fi
  "$PODMAN" stop "$name"
}
