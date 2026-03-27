---
id: github-actions
name: GitHub Actions Expert
category: deploying
level1: "For GitHub Actions workflows — CI/CD pipelines, matrix builds, secrets, reusable workflows"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**GitHub Actions Expert** — Activate for: writing GitHub Actions workflows, CI/CD pipelines, matrix builds, environment secrets, reusable workflows, Docker build and push, staging/prod deployment, caching, concurrency groups.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## GitHub Actions Expert — Core Instructions

1. **Pin actions to a full commit SHA, not a mutable tag** — `actions/checkout@v4` can change under you; `actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683` is immutable. Use SHA pins for all third-party actions in production workflows.
2. **Never hardcode secrets — always use `secrets` context** — reference as `${{ secrets.MY_SECRET }}`. Never echo secrets; GitHub masks known secret values but not derived ones.
3. **Use `concurrency` groups to cancel stale runs** — on push/PR workflows, set `concurrency.cancel-in-progress: true` so a new push cancels the in-flight run for the same branch.
4. **Separate CI (test) from CD (deploy) workflows** — CI runs on every PR; CD runs only on merge to `main` or on explicit tags. Coupling them leads to accidental deploys.
5. **Cache dependencies explicitly** — `actions/cache` keyed on the lockfile hash eliminates redundant installs. Without caching, a 2-minute `npm install` runs on every commit.
6. **Use `environment` for production deploys** — environments enforce required reviewers and scoped secrets, preventing accidental prod deployments from feature branches.
7. **Use `workflow_call` for reusable logic** — extract shared CI steps (lint, test, build) into a reusable workflow called with `uses:` rather than copy-pasting YAML across repositories.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## GitHub Actions Expert — Full Reference

### Workflow File Structure

```
.github/
└── workflows/
    ├── ci.yml               # runs on every PR
    ├── cd.yml               # runs on merge to main / release tag
    ├── release.yml          # builds and publishes releases
    └── _shared-test.yml     # reusable workflow (workflow_call)
```

---

### Full CI Workflow (Node.js example)

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, "release/**"]
  pull_request:
    branches: [main]

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint-and-test:
    name: Lint & Test (Node ${{ matrix.node-version }})
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18, 20, 22]
      fail-fast: false      # run all matrix legs even if one fails

    steps:
      - name: Checkout
        uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2

      - name: Set up Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@cdca7365b2dadb8aad0a33bc7601856ffabcc48e  # v4.3.0
        with:
          node-version: ${{ matrix.node-version }}

      - name: Cache node_modules
        uses: actions/cache@5a3ec84eff668545956fd18022155c47e93e2684  # v4.2.3
        with:
          path: ~/.npm
          key: npm-${{ runner.os }}-${{ matrix.node-version }}-${{ hashFiles('**/package-lock.json') }}
          restore-keys: |
            npm-${{ runner.os }}-${{ matrix.node-version }}-
            npm-${{ runner.os }}-

      - name: Install dependencies
        run: npm ci

      - name: Lint
        run: npm run lint

      - name: Type check
        run: npm run type-check

      - name: Test
        run: npm test -- --coverage

      - name: Upload coverage
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02  # v4.6.2
        with:
          name: coverage-node${{ matrix.node-version }}
          path: coverage/
          retention-days: 7
```

---

### Triggers Reference

```yaml
on:
  # Push to specific branches or tags
  push:
    branches: [main, "release/**"]
    tags: ["v*.*.*"]
    paths-ignore: ["docs/**", "*.md"]

  # Pull requests (default: opened, synchronize, reopened)
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened, ready_for_review]

  # Scheduled (cron in UTC)
  schedule:
    - cron: "0 6 * * 1-5"    # 6am UTC weekdays

  # Manual trigger with inputs
  workflow_dispatch:
    inputs:
      environment:
        description: "Target environment"
        required: true
        default: staging
        type: choice
        options: [staging, production]
      dry_run:
        description: "Dry run — skip actual deploy"
        type: boolean
        default: false

  # Called by another workflow
  workflow_call:
    inputs:
      image_tag:
        required: true
        type: string
    secrets:
      DEPLOY_TOKEN:
        required: true
```

---

### Jobs, Steps, and `needs`

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      image_tag: ${{ steps.meta.outputs.tags }}
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
      - id: meta
        run: echo "tags=myregistry/app:${{ github.sha }}" >> $GITHUB_OUTPUT

  test:
    runs-on: ubuntu-latest
    needs: build            # waits for build to succeed
    steps:
      - run: echo "Running tests..."

  deploy-staging:
    runs-on: ubuntu-latest
    needs: [build, test]    # waits for both
    environment: staging
    steps:
      - run: echo "Deploying ${{ needs.build.outputs.image_tag }} to staging"

  deploy-production:
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment: production  # requires manual approval if configured
    if: github.ref == 'refs/heads/main'
    steps:
      - run: echo "Deploying to production"
```

---

### Secrets and Environment Variables

```yaml
steps:
  # Repository secret
  - name: Login to registry
    run: echo "${{ secrets.REGISTRY_PASSWORD }}" | docker login -u "${{ secrets.REGISTRY_USER }}" --password-stdin

  # Environment-scoped secret (only available when job uses that environment)
  - name: Deploy
    env:
      DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}   # scoped to 'production' environment
    run: ./deploy.sh

  # Set an env var for the rest of the job
  - name: Set image tag
    run: echo "IMAGE_TAG=${{ github.sha }}" >> $GITHUB_ENV

  - name: Use it in next step
    run: docker push myregistry/app:$IMAGE_TAG

  # Pass data between steps via GITHUB_OUTPUT
  - id: compute
    run: echo "result=42" >> $GITHUB_OUTPUT
  - run: echo "Result was ${{ steps.compute.outputs.result }}"
```

---

### Caching Strategies

```yaml
# Node.js — cache npm install
- uses: actions/cache@5a3ec84eff668545956fd18022155c47e93e2684
  with:
    path: ~/.npm
    key: npm-${{ runner.os }}-${{ hashFiles('**/package-lock.json') }}
    restore-keys: npm-${{ runner.os }}-

# Python — cache pip
- uses: actions/cache@5a3ec84eff668545956fd18022155c47e93e2684
  with:
    path: ~/.cache/pip
    key: pip-${{ runner.os }}-${{ hashFiles('**/requirements*.txt') }}

# Docker layer cache (buildx + GitHub cache backend)
- uses: docker/setup-buildx-action@b5730b2a1d2f9a3d4e6ed571e2cd08bb3ad41a68  # v3.10.0
- uses: docker/build-push-action@471d1dc4e07e5cdedd4c2171150001c434f0b7a4  # v6.15.0
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
    push: true
    tags: myregistry/app:${{ github.sha }}
```

---

### Docker Build and Push

```yaml
# .github/workflows/docker.yml
name: Build and Push Docker Image

on:
  push:
    branches: [main]
    tags: ["v*.*.*"]

jobs:
  build-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write   # needed for GitHub Container Registry (ghcr.io)

    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683

      - name: Docker meta
        id: meta
        uses: docker/metadata-action@902fa8ec7d6ecbea4c0e6f894a3b0e8c5ce65593  # v5.7.0
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=sha,prefix=sha-
            type=semver,pattern={{version}}
            type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}

      - name: Log in to GHCR
        uses: docker/login-action@74a5d142397b4f367a81961eba4e8cd7edddf772  # v3.4.0
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@b5730b2a1d2f9a3d4e6ed571e2cd08bb3ad41a68

      - name: Build and push
        uses: docker/build-push-action@471d1dc4e07e5cdedd4c2171150001c434f0b7a4
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

---

### Reusable Workflow (workflow_call)

```yaml
# .github/workflows/_shared-test.yml
name: Shared Test

on:
  workflow_call:
    inputs:
      python-version:
        required: false
        type: string
        default: "3.12"
    secrets:
      TEST_DB_URL:
        required: true
    outputs:
      test-result:
        description: "Pass or fail"
        value: ${{ jobs.test.outputs.result }}

jobs:
  test:
    runs-on: ubuntu-latest
    outputs:
      result: ${{ steps.run.outputs.result }}
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
      - uses: actions/setup-python@42375524b1b0f5686de4dc5c0b9e8e22c4ef76a9  # v5.4.0
        with:
          python-version: ${{ inputs.python-version }}
      - id: run
        env:
          DATABASE_URL: ${{ secrets.TEST_DB_URL }}
        run: |
          pip install -r requirements.txt
          pytest && echo "result=pass" >> $GITHUB_OUTPUT || echo "result=fail" >> $GITHUB_OUTPUT
```

```yaml
# Caller workflow
jobs:
  run-tests:
    uses: ./.github/workflows/_shared-test.yml
    with:
      python-version: "3.12"
    secrets:
      TEST_DB_URL: ${{ secrets.TEST_DB_URL }}
```

---

### Staging / Production Deployment Pattern

```yaml
# .github/workflows/cd.yml
name: Deploy

on:
  push:
    branches: [main]

concurrency:
  group: deploy-${{ github.ref }}
  cancel-in-progress: false    # never cancel an in-flight deploy

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.example.com
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
      - name: Deploy to staging
        env:
          KUBECONFIG_DATA: ${{ secrets.STAGING_KUBECONFIG }}
        run: |
          echo "$KUBECONFIG_DATA" | base64 -d > /tmp/kubeconfig
          export KUBECONFIG=/tmp/kubeconfig
          kubectl set image deployment/api-server api-server=myregistry/app:${{ github.sha }} -n staging
          kubectl rollout status deployment/api-server -n staging

  deploy-production:
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment:
      name: production          # requires reviewer approval in GitHub environment settings
      url: https://example.com
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
      - name: Deploy to production
        env:
          KUBECONFIG_DATA: ${{ secrets.PROD_KUBECONFIG }}
        run: |
          echo "$KUBECONFIG_DATA" | base64 -d > /tmp/kubeconfig
          export KUBECONFIG=/tmp/kubeconfig
          kubectl set image deployment/api-server api-server=myregistry/app:${{ github.sha }} -n production
          kubectl rollout status deployment/api-server -n production
```

---

### Concurrency Groups Reference

```yaml
# Cancel stale PR runs when new commits are pushed
concurrency:
  group: pr-${{ github.event.pull_request.number }}
  cancel-in-progress: true

# Cancel stale branch CI runs
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

# Never cancel in-flight deploys — finish or fail cleanly
concurrency:
  group: deploy-${{ github.ref }}
  cancel-in-progress: false
```

---

### Permissions (Least Privilege)

```yaml
# Top-level default: read-only for everything
permissions:
  contents: read

jobs:
  build:
    permissions:
      contents: read
      packages: write       # push to GHCR
  deploy:
    permissions:
      contents: read
      id-token: write       # OIDC for AWS/GCP keyless auth
```

---

### OIDC Keyless Auth (AWS example)

```yaml
- name: Configure AWS credentials via OIDC
  uses: aws-actions/configure-aws-credentials@e3dd6a429d7300a6a4c196c26e071d42e0343502  # v4.0.2
  with:
    role-to-assume: arn:aws:iam::123456789012:role/github-actions-role
    aws-region: us-east-1
# No long-lived AWS_ACCESS_KEY_ID needed — token is minted per-run
```

---

### Anti-patterns to Avoid
- Using `@v4` or `@main` tags for third-party actions — mutable tags can be hijacked; always pin to a full SHA
- Printing secrets with `echo ${{ secrets.MY_SECRET }}` — even if masked in logs, never echo secrets
- Using `workflow_dispatch` without branch protection — anyone with write access can trigger a production deploy manually
- Setting `cancel-in-progress: true` on deploy workflows — a new push should not cancel an in-progress production deployment mid-flight
- Skipping `needs:` between test and deploy — a deploy can start before tests finish if `needs` is omitted
- Storing kubeconfig or cloud credentials as plain text in repository files — always use `secrets` context or OIDC
- Running everything in a single massive job — split into lint, test, build, deploy jobs so failures are isolated and retries are cheaper
<!-- LEVEL 3 END -->
