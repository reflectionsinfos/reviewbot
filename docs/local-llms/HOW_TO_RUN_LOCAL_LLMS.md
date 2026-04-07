# How to Configure and Run Local LLMs with ReviewBot

This guide covers installing Ollama and running local LLMs for ReviewBot's hybrid routing system, both on a local laptop (Windows/macOS/Linux) and on GCP (Cloud VM or Cloud Run).

---

## Table of Contents

1. [Overview](#overview)
2. [Recommended Models](#recommended-models)
3. [Running Locally (Laptop)](#running-locally-laptop)
4. [Running on GCP Compute Engine VM](#running-on-gcp-compute-engine-vm)
5. [Running on GCP Cloud Run (Sidecar)](#running-on-gcp-cloud-run-sidecar)
6. [Registering Ollama in ReviewBot UI](#registering-ollama-in-reviewbot-ui)
7. [Verifying the Setup](#verifying-the-setup)
8. [Troubleshooting](#troubleshooting)

---

## Overview

ReviewBot's hybrid routing sends **simple checklist items** to a local Ollama instance and reserves **complex or security-sensitive items** for a cloud LLM. This reduces cloud API token usage by ~70%.

```
ReviewBot backend
     │
     ├── Simple items  ──► Ollama  (local/VM/sidecar)  [free, no rate limit]
     └── Complex items ──► Groq / OpenAI / Gemini      [cloud quota preserved]
```

Ollama exposes an **OpenAI-compatible REST API**, so ReviewBot uses the same `AsyncOpenAI` client for both local and cloud calls — no code changes needed.

---

## Recommended Models

| Model | Size | RAM needed | Best for |
|-------|------|-----------|----------|
| `qwen2.5-coder:7b` | ~4.7 GB | 8 GB | Code-focused reviews (recommended) |
| `mistral:7b-instruct` (Q4) | ~4.1 GB | 8 GB | General reviews, lower RAM |
| `llama3.2:3b` | ~2.0 GB | 4 GB | Very low resource, lightweight |
| `qwen2.5-coder:14b` | ~9 GB | 16 GB | Higher quality, more RAM required |

**For development/testing:** `qwen2.5-coder:7b` is the sweet spot — code-aware, fits in 8 GB RAM, runs without a GPU.

---

## Running Locally (Laptop)

### Prerequisites

- Windows 10/11, macOS 12+, or Ubuntu 20.04+
- 8 GB RAM minimum (16 GB recommended)
- ~5 GB free disk space per model

### Step 1 — Install Ollama

**Windows:**
```
Download and run: https://ollama.com/download/windows
```

**macOS:**
```bash
brew install ollama
# or download from https://ollama.com/download/mac
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Step 2 — Pull the model

```bash
ollama pull qwen2.5-coder:7b
```

This downloads ~4.7 GB once and caches it locally.

### Step 3 — Start Ollama

Ollama starts automatically on Windows/macOS after install.  
On Linux, start it manually if not running as a service:

```bash
ollama serve
# Runs on http://localhost:11434 by default
```

Verify it is running:

```bash
curl http://localhost:11434/api/tags
# Should return a JSON list including qwen2.5-coder:7b
```

### Step 4 — Test the OpenAI-compatible endpoint

```bash
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-coder:7b",
    "messages": [{"role": "user", "content": "Say hello"}],
    "max_tokens": 20
  }'
```

Expected: a valid JSON response with `choices[0].message.content`.

### Step 5 — Register in ReviewBot

See [Registering Ollama in ReviewBot UI](#registering-ollama-in-reviewbot-ui).

---

## Running on GCP Compute Engine VM

Use this when you want ReviewBot (Cloud Run) to offload local inference to a dedicated VM.

### Step 1 — Create a VM

```bash
gcloud compute instances create ollama-server \
  --zone=us-central1-a \
  --machine-type=n2-standard-4 \       # 4 vCPU, 16 GB RAM
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --tags=ollama-server
```

> For GPU acceleration (optional):
> Replace `n2-standard-4` with `n1-standard-4` and add `--accelerator=type=nvidia-tesla-t4,count=1 --maintenance-policy=TERMINATE`

### Step 2 — Open firewall (internal VPC only — do not expose publicly)

```bash
gcloud compute firewall-rules create allow-ollama-internal \
  --allow=tcp:11434 \
  --source-ranges=10.0.0.0/8 \        # VPC internal CIDR only
  --target-tags=ollama-server \
  --description="Ollama internal access from Cloud Run VPC connector"
```

**Do NOT expose port 11434 to the internet (0.0.0.0/0). Ollama has no built-in auth.**

### Step 3 — Install Ollama on the VM

SSH into the VM:

```bash
gcloud compute ssh ollama-server --zone=us-central1-a
```

Install and start:

```bash
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl enable ollama
sudo systemctl start ollama
```

By default Ollama listens only on `127.0.0.1:11434`. To allow VPC traffic:

```bash
# Edit the systemd service to bind on all interfaces
sudo mkdir -p /etc/systemd/system/ollama.service.d
cat <<EOF | sudo tee /etc/systemd/system/ollama.service.d/override.conf
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
EOF

sudo systemctl daemon-reload
sudo systemctl restart ollama
```

Pull the model:

```bash
ollama pull qwen2.5-coder:7b
```

### Step 4 — Connect Cloud Run to the VM

Cloud Run needs a **Serverless VPC Access Connector** to reach the VM's internal IP.

```bash
# Create connector (if not already exists)
gcloud compute networks vpc-access connectors create reviewbot-connector \
  --region=us-central1 \
  --subnet=default \
  --subnet-project=YOUR_PROJECT_ID

# Deploy Cloud Run with VPC connector
gcloud run deploy reviewbot-web \
  --vpc-connector=reviewbot-connector \
  --vpc-egress=private-ranges-only \
  ... (other existing flags)
```

### Step 5 — Register in ReviewBot

Use the VM's internal IP as the base URL:

```
Base URL: http://10.X.X.X:11434/v1
Provider: ollama
Model: qwen2.5-coder:7b
Role: local
Priority: 10
```

See [Registering Ollama in ReviewBot UI](#registering-ollama-in-reviewbot-ui).

---

## Running on GCP Cloud Run (Sidecar)

Use this for a **fully serverless** setup where Ollama runs as a sidecar container alongside ReviewBot in the same Cloud Run service.

> **Limitation:** Cloud Run has a 32 GB memory limit per instance and no GPU support (as of 2026). Models larger than ~7B parameters may be too slow. Use the VM approach for anything requiring >8 GB RAM.

### Step 1 — Build an Ollama image with the model baked in

Create `ollama.Dockerfile`:

```dockerfile
FROM ollama/ollama:latest

# Pre-pull the model so it's included in the image
RUN ollama serve & sleep 5 && ollama pull qwen2.5-coder:7b && pkill ollama

EXPOSE 11434
CMD ["ollama", "serve"]
```

Build and push to Artifact Registry:

```bash
docker build -f ollama.Dockerfile -t us-central1-docker.pkg.dev/YOUR_PROJECT/reviewbot/ollama:latest .
docker push us-central1-docker.pkg.dev/YOUR_PROJECT/reviewbot/ollama:latest
```

> The model is baked into the image (~5 GB). Cold starts will be slow. Consider keeping min-instances=1.

### Step 2 — Deploy as multi-container Cloud Run service

Create `cloudrun-multicontainer.yaml`:

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: reviewbot-web
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/container-dependencies: '{"reviewbot":["ollama"]}'
    spec:
      containers:
        - name: reviewbot
          image: us-central1-docker.pkg.dev/YOUR_PROJECT/reviewbot/app:latest
          ports:
            - containerPort: 8080
          env:
            - name: OLLAMA_BASE_URL
              value: "http://localhost:11434/v1"
          resources:
            limits:
              memory: "8Gi"
              cpu: "4"

        - name: ollama
          image: us-central1-docker.pkg.dev/YOUR_PROJECT/reviewbot/ollama:latest
          resources:
            limits:
              memory: "8Gi"
              cpu: "4"
          startupProbe:
            httpGet:
              path: /api/tags
              port: 11434
            initialDelaySeconds: 10
            periodSeconds: 5
            failureThreshold: 12   # 60s timeout for model load
```

Deploy:

```bash
gcloud run services replace cloudrun-multicontainer.yaml --region=us-central1
```

### Step 3 — Register in ReviewBot

Since Ollama is a sidecar (same container group), use `localhost`:

```
Base URL: http://localhost:11434/v1
Provider: ollama
Model: qwen2.5-coder:7b
Role: local
Priority: 10
```

---

## Registering Ollama in ReviewBot UI

Once Ollama is running (via any method above), register it in the ReviewBot admin panel.

### Navigate to LLM Configurations

1. Open ReviewBot → **System Config** → **LLM Configurations**
2. Click **Add Configuration**

### Fill in the form

| Field | Value |
|-------|-------|
| Name | `Ollama Local` (or any label) |
| Provider | `ollama` |
| Base URL | `http://localhost:11434/v1` (or VM IP / `localhost` for sidecar) |
| API Key | *(leave blank — Ollama needs no key)* |
| Model Name | `qwen2.5-coder:7b` |
| Role | `local` |
| Priority | `10` (lower number = higher priority) |
| Strategy Affinity | *(leave blank — handles all strategies)* |
| Enabled | ✓ |

### Priority guidance

ReviewBot processes configs in **ascending priority order**. Typical setup:

| Priority | Name | Role | Notes |
|----------|------|------|-------|
| 10 | Ollama Local | local | First for simple items |
| 20 | Groq (primary) | cloud | Complex items, fast |
| 30 | Groq (backup) | cloud | Failover if primary rate-limited |
| 40 | OpenAI | cloud | Final fallback |

---

## Verifying the Setup

### 1 — Check Ollama is reachable from ReviewBot

Use the **Test Connection** button on the LLM Config card in System Config. It sends a minimal prompt and shows the response.

### 2 — Check the routing plan in a review job

Run a review on one of the sample projects in `sample-projects/`. After completion, check the job detail page — the **Routing Plan** section shows which items were sent to Ollama vs cloud, along with complexity labels.

### 3 — Check logs

**Local:**
```bash
# Ollama server logs
journalctl -u ollama -f       # Linux
# or: ollama serve (foreground, shows requests)
```

**Cloud Run:**
```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND textPayload=~"ollama|local_client|planning"' \
  --project=YOUR_PROJECT \
  --limit=50
```

Look for log lines like:
```
Phase 1 routing plan built: 23 complex, 47 simple
_run_llm_item: item=SEC-01 using config=Groq (complex, cloud-locked)
_run_llm_item: item=DOC-03 using config=Ollama Local (simple)
```

---

## Troubleshooting

### `connection refused` on `localhost:11434`

- Ollama is not running. Start it with `ollama serve` (Linux) or check the system tray (Windows/macOS).
- On a VM: check `OLLAMA_HOST=0.0.0.0:11434` is set in the systemd override.

### `model not found`

```bash
ollama pull qwen2.5-coder:7b
ollama list   # confirm it appears
```

### Ollama is very slow (first request takes >30s)

- Model is loading from disk into RAM — this is normal on first call.
- Subsequent calls are fast (model stays resident in memory).
- On Cloud Run sidecar: add `startupProbe` (shown above) so traffic only routes after the model is loaded.

### Cloud Run cannot reach VM Ollama

- Verify the Serverless VPC Access Connector is attached to the Cloud Run service.
- Check the firewall rule allows TCP 11434 from the VPC CIDR (not just the connector subnet).
- Ping the VM internal IP from a Cloud Shell session in the same VPC.

### Planning LLM call fails — all items fall back to cloud

- If the planning call fails, ReviewBot logs a warning and routes **all** `llm_analysis` items to the cloud chain (safe fallback).
- Check for: rate limit on planning config, bad model name, network timeout.
- The planning config prefers Ollama if available, so verify Ollama is responding.

### High memory usage / OOM on VM

- Switch to a Q4 quantized model: `ollama pull mistral:7b-instruct:q4_0`
- Or use a smaller model: `ollama pull llama3.2:3b`
- Increase VM memory (upgrade to `n2-standard-8` or higher).

---

## Quick Reference

```bash
# Install Ollama (Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Pull recommended model
ollama pull qwen2.5-coder:7b

# Start server
ollama serve

# List downloaded models
ollama list

# Test API
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5-coder:7b","messages":[{"role":"user","content":"hello"}],"max_tokens":10}'

# Remove a model (free disk space)
ollama rm qwen2.5-coder:7b
```
