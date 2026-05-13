# Workspace CI

Workspace CI belongs in the workspace repository.

The Archive repo stays an external, pinned toolchain. Local workspace use should prefer the installed `archive` CLI; CI can call `make -C archive ...` against a pinned checkout when that is clearer for the job layout.

## Recommended Ownership

The workspace repo CI should:

1. check out the workspace repo
2. check out the Archive repo at a pinned tag or commit
3. run Archive with `WORKSPACE` pointing at the workspace repo and `ARCHIVE_INSTANCE` selecting the generated-output namespace
4. build the static site
5. package the runtime image from the prebuilt `site/`
6. push the image and optionally deploy it to Kubernetes

## Minimal Checkout Layout

```text
workspace/
  workspace-repo/
    incoming/
    sources/
  archive/
    Makefile
    scripts/
    .vitepress/
    .instances/
    content/
    site/
```

The workspace repo owns canonical content.
The Archive repo owns tooling and generated output.

When you build from one Archive clone against one or more workspace repos, `ARCHIVE_INSTANCE` selects the generated-output namespace inside the Archive repo.
In workspace mode, generated output lands under `.instances/<instance>/...`.

## Build Sequence

From the checked-out Archive repo:

```sh
make WORKSPACE=../workspace-repo ARCHIVE_INSTANCE=workspace-repo validate
make WORKSPACE=../workspace-repo ARCHIVE_INSTANCE=workspace-repo build
make ARCHIVE_INSTANCE=workspace-repo runtime-build
```

Important contract:

- `make build` reads canonical content from the workspace repo and writes generated output into the Archive repo, under `.instances/<instance>/...` in workspace mode
- `make runtime-build` packages the prebuilt `site/` output and does not rebuild canonical content inside the image build

Recommended sequence:

1. `make WORKSPACE=../workspace-repo ARCHIVE_INSTANCE=workspace-repo validate`
2. `make WORKSPACE=../workspace-repo ARCHIVE_INSTANCE=workspace-repo build`
3. `make ARCHIVE_INSTANCE=workspace-repo runtime-build`
4. push the runtime image

If the same Archive checkout is used for multiple workspace builds in one CI environment, give each build a distinct `ARCHIVE_INSTANCE` value.

## Pin Archive

Do not build workspace CI against unpinned Archive `main`.

Pin Archive by:

- release tag such as `v.1.5.0`
- exact commit SHA when testing unreleased changes

Example pinned refs:

- `ARCHIVE_REF=v.1.5.0`
- `ARCHIVE_REF=9f3c2a7b7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a`

## Concrete CI Example

Example GitHub Actions job in the workspace repo:

```yaml
name: build-workspace-archive-site

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    env:
      ARCHIVE_REF: v.1.5.0
      ARCHIVE_INSTANCE: workspace-repo
      ARCHIVE_IMAGE: ghcr.io/example/workspace-archive-site:${{ github.sha }}
    steps:
      - name: Check out workspace repo
        uses: actions/checkout@v4
        with:
          path: workspace-repo

      - name: Check out pinned Archive toolchain
        uses: actions/checkout@v4
        with:
          repository: example/archive
          ref: ${{ env.ARCHIVE_REF }}
          path: archive

      - name: Install Podman
        run: sudo apt-get update && sudo apt-get install -y podman make

      - name: Build static site from workspace content
        run: make -C archive WORKSPACE=../workspace-repo ARCHIVE_INSTANCE=${{ env.ARCHIVE_INSTANCE }} build

      - name: Package runtime image from prebuilt site
        run: |
          make -C archive ARCHIVE_INSTANCE=${{ env.ARCHIVE_INSTANCE }} runtime-build
          podman tag archive-runtime:${{ env.ARCHIVE_INSTANCE }} "$ARCHIVE_IMAGE"

      - name: Push image
        run: podman push "$ARCHIVE_IMAGE"
```

Adjust:

- `repository: example/archive` to your Archive repository location
- `ARCHIVE_INSTANCE` to a stable generated-output namespace for this workspace build
- `ARCHIVE_IMAGE` to your registry destination
- authentication and deployment steps to match your registry and cluster

## Final Artifact

The final deployment artifact is a static site image served by Caddy.

- canonical Markdown does not need to ship in the runtime image
- workspace `incoming/` and `sources/` do not need to be present in the runtime image build context

## Kubernetes Pattern

The Kubernetes-facing flow is intentionally simple:

1. build the site in CI
2. package the runtime image
3. push the image to a registry
4. deploy the image to Kubernetes

Editing does not happen in-cluster.

## Local Makefile Option

If the workspace repo uses the generated forwarding `Makefile`, local commands can be run from the workspace repo directly.

CI can still call Archive directly with `make -C ../archive WORKSPACE=$PWD ...` when that is clearer for the job layout.
