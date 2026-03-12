# AWS Deployment Plan — agent-tracking

## Context
The project is currently local-only. The goal is to deploy it on AWS so anyone can use it to track their own codebase evolution via the dashboard. Each user pushes their own generated data from their local machine; the dashboard on AWS reads it back — isolated per user.

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

---

## Implementation Steps

### Step 1 — Storage abstraction (`src/agent_tracking/storage.py`)
New module with two backends, switched via `STORAGE_BACKEND` env var:
- `local` (default): reads from `ROOT_DIR/visualizations/` — zero-friction local dev
- `s3`: reads from `s3://{S3_BUCKET}/{S3_USER_PREFIX}/visualizations/` via boto3

Interface:
- `read_text(filename)` / `file_exists(filename)` / `list_files(pattern)` / `write_file(filename, content)`

New env vars: `STORAGE_BACKEND`, `S3_BUCKET`, `S3_USER_PREFIX`

---

### Step 2 — Modify `app/server.py`
- Replace all `Path`/`DATA_DIR` reads with `storage.*` calls
- `S3_USER_PREFIX` resolved per-request from authenticated `user_id` (not a global)
- Remove unused `GRAPH_FILE` constant

---

### Step 3 — Auth middleware in `app/server.py`
API key auth via `X-API-Key` header:
- Keys stored in SSM Parameter Store at `/agent-tracking/users/{api_key}` → value is `user_id`
- In-memory cache loaded at startup, refreshed every 5 min via background task
- All routes get `Depends(get_current_user)` → returns `user_id`
- If `STORAGE_BACKEND=local`: auth skipped (returns dummy user for dev)
- `/health` endpoint added — no auth, for ALB health checks

---

### Step 4 — CLI `push` command (`src/agent_tracking/cli.py`)
New subcommand:
```
agent-tracking push --user-id alice --bucket agent-tracking-data [--visualizations-dir ./visualizations] [--region eu-west-1]
```
- Uploads all `*.json` and `*.html` from `visualizations/` to `s3://{bucket}/{user_id}/visualizations/`
- Credentials via standard boto3 chain (`~/.aws/credentials` or env vars)

---

### Step 5 — Update `generate-diagrams.sh`
Add at the end:
```bash
poetry -C "$PROJECT_ROOT" run agent-tracking push \
    --user-id "${AGENT_USER_ID:-$USER}" \
    --bucket "${S3_BUCKET:-agent-tracking-data}"
```
New env vars for users to set: `AGENT_USER_ID`, `S3_BUCKET`

---

### Step 6 — `Dockerfile`
```
FROM python:3.11-slim
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --only main --no-root
COPY src/ ./src/
COPY app/ ./app/
EXPOSE 8080
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8080"]
```
No `visualizations/` directory in image — all data comes from S3.

---

### Step 7 — Add `boto3` to `pyproject.toml`
```toml
boto3 = "^1.34"
```

---

### Step 8 — Terraform infrastructure (`infra/`)

| Resource | Purpose |
|---|---|
| `aws_s3_bucket` | Data storage, one bucket, per-user prefixes |
| `aws_ecs_cluster` + task + service | Fargate, 256 CPU / 512 MB, 1 task |
| `aws_alb` + listener + target group | HTTPS termination, health check on `/health` |
| `aws_iam_role` (task role) | S3 read + SSM read for ECS tasks |
| `aws_iam_user` (push user, one per user) | S3 write scoped to `{user_id}/*` only |
| `aws_ssm_parameter` | API key → user_id mapping |
| VPC S3 gateway endpoint | Free, avoids NAT for S3 calls |
| VPC SSM interface endpoint | Avoids NAT for SSM calls |

Task role permissions (read-only):
- `s3:GetObject`, `s3:ListBucket` on `arn:aws:s3:::agent-tracking-data/*`
- `ssm:GetParametersByPath` on `/agent-tracking/users/`

Push IAM user permissions (write-only, scoped):
- `s3:PutObject` on `arn:aws:s3:::agent-tracking-data/{username}/*`

Files: `infra/main.tf`, `infra/ecs.tf`, `infra/alb.tf`, `infra/iam.tf`, `infra/variables.tf`, `infra/outputs.tf`

---

### Step 9 — ECR + deploy
```bash
aws ecr create-repository --repository-name agent-tracking
docker build -t agent-tracking .
docker tag agent-tracking:latest {account}.dkr.ecr.{region}.amazonaws.com/agent-tracking:latest
docker push ...
terraform -chdir=infra apply
```

---

## Auth + S3 Isolation Flow

```
1. GET / with X-API-Key: abc123
2. FastAPI: cache["abc123"] → user_id = "alice"
3. load_metrics(user_id="alice")
   → s3://agent-tracking-data/alice/visualizations/metrics-id-42.json
4. Push IAM policy prevents alice from writing to bob's prefix
```

---

## Files to Create / Modify

| File | Action |
|---|---|
| `src/agent_tracking/storage.py` | Create |
| `app/server.py` | Modify |
| `src/agent_tracking/cli.py` | Modify — add `push` command |
| `generate-diagrams.sh` | Modify — add push step |
| `Dockerfile` | Create |
| `pyproject.toml` | Modify — add boto3 |
| `infra/main.tf` | Create |
| `infra/ecs.tf` | Create |
| `infra/alb.tf` | Create |
| `infra/iam.tf` | Create |
| `infra/variables.tf` + `outputs.tf` | Create |

---

## Verification

1. **Local**: `STORAGE_BACKEND=local uvicorn app.server:app --reload` → dashboard loads from `visualizations/`
2. **S3 push**: `agent-tracking push --user-id test --bucket my-bucket` → files appear in S3
3. **S3 read**: `STORAGE_BACKEND=s3 S3_BUCKET=my-bucket S3_USER_PREFIX=test uvicorn ...` → dashboard reads from S3
4. **Auth**: `curl -H "X-API-Key: bad" /` → 403; valid key → 200
5. **Docker**: `docker build . && docker run -p 8080:8080 -e STORAGE_BACKEND=s3 ...`
6. **Terraform**: `terraform plan` shows expected resources; `apply` → ALB DNS resolves to dashboard
