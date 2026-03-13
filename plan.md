# AWS Deployment Plan — agent-tracking

> **Scope: Experiment**
> This deployment is an AWS experiment — not a production setup. The goal is to validate the architecture (S3 storage, ECS Fargate, ALB, auth via SSM) on a real environment, not to serve end users at scale. Cost, availability, and security hardening are secondary concerns for now.

## Context

The project is currently local-only. The goal is to deploy it on AWS so anyone can use it to track their own codebase evolution via the dashboard. Each user pushes their own generated data from their local machine; the dashboard on AWS reads it back — isolated per user.

The key design constraint is **per-user data isolation**: all visualization files (metrics, graphs, history) live under a user-specific prefix in S3, and the API enforces that a user can only read their own data. This is achieved without a database — S3 prefixes act as namespaces.

---

## Architecture

```
[Local machine]                         [AWS]
generate-diagrams.sh
  → agent-tracking visualize            ALB (HTTPS)
  → agent-tracking map                    → ECS Fargate (FastAPI app/)
  → agent-tracking history                    → reads from S3
  → agent-tracking push  ──boto3──►  s3://agent-tracking-data/{user_id}/visualizations/
```

The local machine generates all artifacts (JSON metrics, HTML graphs, conversation history) and pushes them to S3. The ECS container only reads from S3 — it never writes. This keeps the server stateless and easy to scale or replace.

---

## Implementation Steps

### Step 1 — Storage abstraction (`src/agent_tracking/storage.py`)

**Why:** Currently `app/server.py` reads files directly from the local `visualizations/` folder using `Path` objects. To support S3 without rewriting every read operation, we introduce a thin abstraction layer that both backends implement identically.

**How:** A new module `storage.py` exposes two classes — `LocalStorage` and `S3Storage` — with the same interface. A factory function `get_storage()` returns the right one based on the `STORAGE_BACKEND` env var.

Backend selection via `STORAGE_BACKEND`:
- `local` (default): reads from `ROOT_DIR/visualizations/` — zero-friction local dev, no AWS credentials needed
- `s3`: reads from `s3://{S3_BUCKET}/{S3_USER_PREFIX}/visualizations/` via boto3

Interface (identical for both backends):
- `read_text(filename)` → returns file content as string
- `file_exists(filename)` → returns bool
- `list_files(pattern)` → returns list of filenames matching a glob, sorted by most recent first
- `write_file(filename, content)` → writes content (used by push, not the server)

New env vars: `STORAGE_BACKEND`, `S3_BUCKET`, `S3_USER_PREFIX`

**Important:** boto3 is only imported inside `S3Storage.__init__`, so local mode works without boto3 installed.

---

### Step 2 — Modify `app/server.py`

**Why:** All current file reads use `Path` objects and `DATA_DIR` directly (e.g. `file.read_text()`, `DATA_DIR.glob(...)`). These need to be replaced with `storage.*` calls so the same code works whether data is on disk or in S3.

**What changes:**
- Each route handler creates a `storage` instance via `get_storage(user_prefix=user_id, local_base_dir=DATA_DIR)`
- `load_metrics(storage)`, `load_graph_data(storage)`, `load_agent_tasks(storage)` all receive the storage instance as a parameter instead of reading `DATA_DIR` directly
- `_tasks_file()` (which returns a `Path`) is replaced by `_tasks_filename(storage)` which returns just a filename string
- `GRAPH_FILE` constant removed — it was unused
- `get_latest_task_id_from_json(storage)` updated to use `storage.read_text()` and `storage.file_exists()`

**Result:** Switching from local to S3 requires only changing the `STORAGE_BACKEND` env var — no code changes.

---

### Step 3 — Auth middleware in `app/server.py`

**Why:** On AWS, the dashboard is public-facing. Without auth, anyone could read any user's data. We need a simple mechanism to identify who is making the request and route them to their own S3 prefix.

**How:** API key authentication via the `X-API-Key` HTTP header. Keys are stored in AWS SSM Parameter Store (not hardcoded), so adding/revoking a user doesn't require a redeployment.

SSM parameter structure:
```
/agent-tracking/users/{api_key}  →  value: user_id
```
For example: `/agent-tracking/users/abc123` → `"alice"`

**In-memory cache:** At startup, the server loads all keys from SSM into a dict `_api_key_cache`. A background asyncio task refreshes it every 5 minutes. This avoids an SSM API call on every request while keeping keys reasonably fresh.

**FastAPI dependency:**
```python
async def get_current_user(x_api_key: str = Header(None)) -> str:
    if STORAGE_BACKEND != "s3":
        return "local"   # auth skipped in local dev
    if not x_api_key or x_api_key not in _api_key_cache:
        raise HTTPException(status_code=403)
    return _api_key_cache[x_api_key]
```
All routes receive `user_id: str = Depends(get_current_user)` and pass it to `get_storage()`.

**`/health` endpoint:** Added without auth so the ALB target group health check can reach it. Without this, ECS tasks would never be marked healthy and the service would never start.

---

### Step 4 — CLI `push` command (`src/agent_tracking/cli.py`)

**Why:** Users generate visualization files locally with `generate-diagrams.sh`. They need a simple way to upload those files to S3 so the dashboard on AWS can read them.

**How:** New `push` subcommand added to the existing CLI:
```
agent-tracking push \
  --user-id alice \
  --bucket agent-tracking-data \
  [--visualizations-dir ./visualizations] \
  [--region eu-west-1]
```

What it does:
- Iterates over all `*.json` and `*.html` files in `--visualizations-dir`
- Uploads each to `s3://{bucket}/{user_id}/visualizations/{filename}`
- Uses the standard boto3 credential chain — no extra config needed if `~/.aws/credentials` is set up or env vars (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) are present

The IAM user created in Step 8 only has `s3:PutObject` on their own prefix, so even if credentials leak, they cannot overwrite other users' data.

---

### Step 5 — Update `generate-diagrams.sh`

**Why:** The script is the main entry point for the analysis pipeline. To make push seamless, it should automatically upload to S3 after generating the files — but only if the user has configured an S3 bucket (opt-in via env var).

**What's added at the end of the script:**
```bash
if [ -n "${S3_BUCKET:-}" ]; then
    poetry -C "$PROJECT_ROOT" run agent-tracking push \
        --user-id "${AGENT_USER_ID:-$USER}" \
        --bucket "${S3_BUCKET:-agent-tracking-data}"
fi
```

The push is **conditional** — if `S3_BUCKET` is not set, the script behaves exactly as before (local only). Users who want to push to AWS simply export:
```bash
export S3_BUCKET=agent-tracking-data
export AGENT_USER_ID=alice   # defaults to $USER if not set
```

---

### Step 6 — `Dockerfile`

**Why:** ECS Fargate requires a container image. The image must contain the FastAPI app and all Python dependencies, but NOT the `visualizations/` folder — all data comes from S3 at runtime.

**Key decisions:**
- `python:3.11-slim` — small base image, matches the project's Python version
- Poetry is used to install dependencies (consistent with local dev)
- `--only main` — dev dependencies (pytest, black, ruff, mypy) are excluded from the image
- `--no-root` — the package itself doesn't need to be installed since `server.py` uses `sys.path.insert` to find `src/`
- Dependencies are installed before copying source code — this layer is cached by Docker and only rebuilt when `pyproject.toml` or `poetry.lock` changes

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install poetry==1.8.3
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --only main --no-root
COPY src/ ./src/
COPY app/ ./app/
EXPOSE 8080
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

### Step 7 — Add `boto3` to `pyproject.toml`

**Why:** boto3 is the AWS SDK for Python, required by `S3Storage` and the `push` command. It is not currently a dependency.

```toml
boto3 = "^1.34"
```

Added under `[tool.poetry.dependencies]`. This also ensures it is included in the Docker image via `poetry install --only main`.

---

### Step 8 — Terraform infrastructure (`infra/`)

**Why:** Rather than clicking through the AWS console, Terraform lets us declare the full infrastructure as code — reproducible, reviewable, and easy to tear down after the experiment.

**Resources created:**

| Resource | Purpose |
|---|---|
| `aws_s3_bucket` | Single bucket for all users; isolation via prefixes (`{user_id}/visualizations/`) |
| `aws_ecs_cluster` + task + service | Runs the FastAPI container on Fargate (serverless, no EC2 to manage) |
| `aws_alb` + listener + target group | Receives HTTPS traffic and forwards to ECS; health check on `/health` |
| `aws_iam_role` (task role) | Grants the ECS container permission to read S3 and SSM |
| `aws_iam_user` (one per user) | Push credentials — write-only, scoped to their own S3 prefix |
| `aws_ssm_parameter` | Stores `api_key → user_id` mappings for auth |
| VPC S3 gateway endpoint | Routes S3 traffic inside AWS network — free, no NAT Gateway needed |
| VPC SSM interface endpoint | Routes SSM traffic inside AWS network — avoids NAT Gateway cost |

**Task role permissions (ECS container — read-only):**
- `s3:GetObject`, `s3:ListBucket` on `arn:aws:s3:::agent-tracking-data/*`
- `ssm:GetParametersByPath` on `/agent-tracking/users/`

**Push IAM user permissions (local machine — write-only, scoped):**
- `s3:PutObject` on `arn:aws:s3:::agent-tracking-data/{username}/*`
- Cannot read, delete, or write to other users' prefixes

**Fargate sizing (experiment):** 256 CPU units (0.25 vCPU), 512 MB RAM, 1 task. Sufficient for a dashboard with a handful of users. Cost: ~$5–10/month.

**Files:** `infra/main.tf`, `infra/ecs.tf`, `infra/alb.tf`, `infra/iam.tf`, `infra/variables.tf`, `infra/outputs.tf`

---

### Step 9 — ECR + deploy

**Why:** ECS needs to pull the image from a container registry. ECR (Elastic Container Registry) is the native AWS option — no extra auth setup needed when the ECS task role has ECR pull permissions.

**Steps:**
```bash
# 1. Create the registry
aws ecr create-repository --repository-name agent-tracking

# 2. Build the image locally
docker build -t agent-tracking .

# 3. Tag and push to ECR
docker tag agent-tracking:latest {account}.dkr.ecr.{region}.amazonaws.com/agent-tracking:latest
aws ecr get-login-password | docker login --username AWS --password-stdin {account}.dkr.ecr.{region}.amazonaws.com
docker push {account}.dkr.ecr.{region}.amazonaws.com/agent-tracking:latest

# 4. Deploy infrastructure
terraform -chdir=infra init
terraform -chdir=infra plan
terraform -chdir=infra apply
```

After `apply`, Terraform outputs the ALB DNS name. The dashboard is accessible at `https://{alb-dns}/`.

---

## Auth + S3 Isolation Flow

```
1. GET / with X-API-Key: abc123
2. FastAPI middleware: _api_key_cache["abc123"] → user_id = "alice"
3. get_storage(user_prefix="alice") → S3Storage(prefix="alice")
4. load_metrics() → s3://agent-tracking-data/alice/visualizations/metrics-id-42.json
5. Push IAM policy: alice's credentials can only PutObject under alice/* → cannot touch bob's data
```

The server never sees a path like `bob/visualizations/` for a request authenticated as `alice` — the storage instance is scoped to the authenticated user for the entire request lifecycle.

---

## Files to Create / Modify

| File | Action |
|---|---|
| `src/agent_tracking/storage.py` | Create — S3/local abstraction |
| `app/server.py` | Modify — use storage, add auth middleware, add `/health` |
| `src/agent_tracking/cli.py` | Modify — add `push` subcommand |
| `generate-diagrams.sh` | Modify — add conditional push step at end |
| `Dockerfile` | Create |
| `pyproject.toml` | Modify — add boto3 dependency |
| `infra/main.tf` | Create — provider, S3, VPC endpoints |
| `infra/ecs.tf` | Create — cluster, task definition, service |
| `infra/alb.tf` | Create — ALB, listener, target group |
| `infra/iam.tf` | Create — task role, push IAM users |
| `infra/variables.tf` + `outputs.tf` | Create — input vars and outputs |

---

## Verification

1. **Local (no AWS):** `STORAGE_BACKEND=local uvicorn app.server:app --reload` → dashboard loads from `visualizations/`, no auth required
2. **S3 push:** `agent-tracking push --user-id test --bucket my-bucket` → files appear under `test/visualizations/` in S3
3. **S3 read:** `STORAGE_BACKEND=s3 S3_BUCKET=my-bucket S3_USER_PREFIX=test uvicorn app.server:app` → dashboard reads from S3
4. **Auth:** `curl -H "X-API-Key: bad" http://localhost:8000/` → 403; valid key → 200
5. **Docker:** `docker build . && docker run -p 8080:8080 -e STORAGE_BACKEND=s3 -e S3_BUCKET=... -e AWS_ACCESS_KEY_ID=... agent-tracking`
6. **Terraform:** `terraform plan` shows expected resources; `apply` → ALB DNS resolves to the dashboard
