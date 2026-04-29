# Private CI

Private CI belongs in the private content repository.

The public Archive repo stays an external, pinned toolchain.

## Recommended Ownership

The private repo CI should:

1. check out the private content repo
2. check out the public Archive repo at a pinned tag or commit
3. run Archive with `WORKSPACE` pointing at the private repo
4. build the static site
5. package the runtime image from the prebuilt `site/`
6. push the image and optionally deploy it to Kubernetes

## Minimal Checkout Layout

```text
workspace/
  private-content/
    incoming/
    sources/
  archive/
    Makefile
    scripts/
    .vitepress/
    content/
    site/
```

The private repo owns canonical content.
The Archive repo owns tooling and generated output.

## Build Sequence

From the checked-out Archive repo:

```sh
make WORKSPACE=../private-content validate
make WORKSPACE=../private-content build
make runtime-build
```

Important contract:

- `make build` reads canonical content from the private repo and writes generated `content/` and `site/` output into the Archive repo
- `make runtime-build` packages the prebuilt `site/` output and does not rebuild canonical content inside the image build

Recommended sequence:

1. `make WORKSPACE=../private-content validate`
2. `make WORKSPACE=../private-content build`
3. `make runtime-build`
4. push the runtime image

## Pin Archive

Do not build private CI against unpinned Archive `main`.

Pin Archive by:

- release tag such as `v1.0.0`
- exact commit SHA when testing unreleased changes

Example pinned refs:

- `ARCHIVE_REF=v1.0.0`
- `ARCHIVE_REF=9f3c2a7b7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a`

## Concrete CI Example

Example GitHub Actions job in the private repo:

```yaml
name: build-private-archive-site

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    env:
      ARCHIVE_REF: v1.0.0
      ARCHIVE_IMAGE: ghcr.io/example/private-archive-site:${{ github.sha }}
    steps:
      - name: Check out private content repo
        uses: actions/checkout@v4
        with:
          path: private-content

      - name: Check out pinned Archive toolchain
        uses: actions/checkout@v4
        with:
          repository: example/archive
          ref: ${{ env.ARCHIVE_REF }}
          path: archive

      - name: Install Podman
        run: sudo apt-get update && sudo apt-get install -y podman make

      - name: Build static site from private content
        run: make -C archive WORKSPACE=../private-content build

      - name: Package runtime image from prebuilt site
        run: |
          make -C archive runtime-build
          podman tag archive-runtime:local "$ARCHIVE_IMAGE"

      - name: Push image
        run: podman push "$ARCHIVE_IMAGE"
```

Adjust:

- `repository: example/archive` to your public Archive repository location
- `ARCHIVE_IMAGE` to your registry destination
- authentication and deployment steps to match your registry and cluster

## Final Artifact

The final deployment artifact is a static site image served by Caddy.

- canonical Markdown does not need to ship in the runtime image
- private `incoming/` and `sources/` do not need to be present in the runtime image build context

## Kubernetes Pattern

The Kubernetes-facing flow is intentionally simple:

1. build the site in CI
2. package the runtime image
3. push the image to a registry
4. deploy the image to Kubernetes

Editing does not happen in-cluster.

## Wrapper Makefile Option

If the private repo uses the generated forwarding `Makefile`, local commands can be run from the private repo directly.

CI can still call Archive directly with `make -C ../archive WORKSPACE=$PWD ...` when that is clearer for the job layout.
